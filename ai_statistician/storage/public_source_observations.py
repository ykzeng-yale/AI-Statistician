from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..fingerprint import stable_hash


class ResearchSourceDiscoveryError(RuntimeError, ValueError):
    """A public-source provider or durable-observation failure."""


PublicSourceObservationStoreError = ResearchSourceDiscoveryError


_READ_FIELDS = (
    "provider",
    "source_handle",
    "source_kind",
    "source_identity",
    "title",
    "url",
    "publication_date",
    "citation",
    "revision",
    "path",
    "content",
)


class PublicSourceObservationStore:
    """Pin exact public-source observations for workspace continuation."""

    def __init__(
        self,
        *,
        state_dir: Path | None,
        provider: str,
        source_horizon: str,
        max_content_bytes: int,
        proof_evidence_status: str,
    ) -> None:
        self.provider = provider
        self.source_horizon = source_horizon
        self.max_content_bytes = max_content_bytes
        self.proof_evidence_status = proof_evidence_status
        self._db_path = (
            state_dir.resolve() / "observations.sqlite3"
            if state_dir is not None
            else None
        )
        self._results: dict[str, dict[str, Any]] = {}
        self._reads: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._revisions: dict[str, set[str]] = {}
        self._snapshots: dict[tuple[str, str], dict[str, Any]] = {}
        if self._db_path is not None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    @property
    def durable(self) -> bool:
        return self._db_path is not None

    def result(self, source_handle: str) -> Mapping[str, Any] | None:
        row = self._results.get(source_handle)
        return dict(row) if row is not None else None

    def pin_results(
        self, rows: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        pinned = []
        for candidate in rows:
            handle = str(candidate["source_handle"])
            row = self._results.setdefault(handle, dict(candidate))
            self._persist_result(row)
            pinned.append(dict(row))
        return pinned

    def read(
        self, source_handle: str, revision: str, path: str
    ) -> Mapping[str, Any] | None:
        row = self._reads.get((source_handle, revision, path))
        return dict(row) if row is not None else None

    def read_for_path(
        self, source_handle: str, path: str
    ) -> Mapping[str, Any] | None:
        matches = [
            row
            for (handle, _revision, stored_path), row in self._reads.items()
            if handle == source_handle and stored_path == path
        ]
        if len(matches) > 1:
            raise PublicSourceObservationStoreError(
                "public source has ambiguous pinned revisions"
            )
        return dict(matches[0]) if matches else None

    def revisions(self, source_handle: str) -> set[str]:
        return set(self._revisions.get(source_handle, set()))

    def snapshot(self, source_handle: str, revision: str) -> Mapping[str, Any] | None:
        row = self._snapshots.get((source_handle, revision))
        return dict(row) if row is not None else None

    def pin_snapshot(
        self, source_handle: str, revision: str, descriptor: Mapping[str, Any]
    ) -> None:
        if revision not in self.revisions(source_handle):
            raise PublicSourceObservationStoreError("snapshot revision was not observed")
        key, row = (source_handle, revision), dict(descriptor)
        if key in self._snapshots and self._snapshots[key] != row:
            raise PublicSourceObservationStoreError("acquired source snapshot changed")
        if self._db_path is not None:
            values = (*key, _json(row), stable_hash(row))
            try:
                with sqlite3.connect(self._db_path, timeout=5.0) as database:
                    database.execute(
                        "INSERT OR IGNORE INTO source_snapshots VALUES (?, ?, ?, ?)", values
                    )
                    actual = database.execute(
                        "SELECT * FROM source_snapshots WHERE source_handle = ? AND revision = ?",
                        key,
                    ).fetchone()
            except sqlite3.DatabaseError as exc:
                raise PublicSourceObservationStoreError("source snapshot could not be stored") from exc
            if actual != values:
                raise PublicSourceObservationStoreError("acquired source snapshot changed")
        self._snapshots[key] = row

    def remember_read(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        stored = {field: observation[field] for field in _READ_FIELDS}
        content = str(stored["content"])
        if len(content.encode("utf-8")) > self.max_content_bytes:
            raise PublicSourceObservationStoreError(
                "public source observation exceeds its durable byte limit"
            )
        key = (
            str(stored["source_handle"]),
            str(stored["revision"]),
            str(stored["path"]),
        )
        existing = self._reads.get(key)
        if existing is not None and existing != stored:
            raise PublicSourceObservationStoreError(
                "public source bytes changed for an exact identity"
            )
        self._reads[key] = stored
        if stored["source_kind"] == "repository":
            self._revisions.setdefault(key[0], set()).add(key[1])
        self._persist_read(stored)
        return dict(stored)

    def _persist_result(self, row: Mapping[str, Any]) -> None:
        if self._db_path is None:
            return
        values = (
            str(row["source_handle"]),
            _json(row),
            stable_hash(dict(row)),
        )
        try:
            with sqlite3.connect(self._db_path, timeout=5.0) as database:
                database.execute(
                    "INSERT OR IGNORE INTO source_results VALUES (?, ?, ?)", values
                )
                actual = database.execute(
                    "SELECT source_handle, row_json, row_hash FROM source_results "
                    "WHERE source_handle = ?",
                    values[:1],
                ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise PublicSourceObservationStoreError(
                "public source result could not be stored"
            ) from exc
        if actual != values:
            raise PublicSourceObservationStoreError(
                "public source identity contains different metadata"
            )

    def _persist_read(self, stored: Mapping[str, Any]) -> None:
        if self._db_path is None:
            return
        content = str(stored["content"]).encode("utf-8")
        metadata = {
            field: stored[field]
            for field in _READ_FIELDS
            if field != "content"
        }
        metadata.update(
            {
                "schema_version": 1,
                "artifact_kind": "PublicResearchSourceExactObservation",
                "proof_evidence_status": self.proof_evidence_status,
            }
        )
        values = (
            stored["source_handle"],
            stored["revision"],
            stored["path"],
            _json(metadata),
            stable_hash(metadata),
            content,
            hashlib.sha256(content).hexdigest(),
        )
        try:
            with sqlite3.connect(self._db_path, timeout=5.0) as database:
                database.execute(
                    "INSERT OR IGNORE INTO source_reads VALUES (?, ?, ?, ?, ?, ?, ?)",
                    values,
                )
                actual = database.execute(
                    "SELECT source_handle, revision, source_path, metadata_json, "
                    "metadata_hash, content, content_sha256 FROM source_reads "
                    "WHERE source_handle = ? AND revision = ? AND source_path = ?",
                    values[:3],
                ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise PublicSourceObservationStoreError(
                "public source observation could not be stored"
            ) from exc
        if actual != values:
            raise PublicSourceObservationStoreError(
                "public source bytes changed for an exact identity"
            )

    def _load(self) -> None:
        assert self._db_path is not None
        try:
            with sqlite3.connect(self._db_path, timeout=5.0) as database:
                database.execute(
                    "CREATE TABLE IF NOT EXISTS store_metadata "
                    "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                database.execute(
                    "CREATE TABLE IF NOT EXISTS source_results "
                    "(source_handle TEXT PRIMARY KEY, row_json TEXT NOT NULL, "
                    "row_hash TEXT NOT NULL)"
                )
                database.execute(
                    "CREATE TABLE IF NOT EXISTS source_reads "
                    "(source_handle TEXT NOT NULL, revision TEXT NOT NULL, "
                    "source_path TEXT NOT NULL, metadata_json TEXT NOT NULL, "
                    "metadata_hash TEXT NOT NULL, content BLOB NOT NULL, "
                    "content_sha256 TEXT NOT NULL, "
                    "PRIMARY KEY (source_handle, revision, source_path))"
                )
                database.execute(
                    "CREATE TABLE IF NOT EXISTS source_snapshots "
                    "(source_handle TEXT NOT NULL, revision TEXT NOT NULL, "
                    "descriptor_json TEXT NOT NULL, descriptor_hash TEXT NOT NULL, "
                    "PRIMARY KEY (source_handle, revision))"
                )
                for key, expected in (
                    ("schema_version", "1"),
                    ("provider", self.provider),
                    ("source_horizon", self.source_horizon),
                ):
                    database.execute(
                        "INSERT OR IGNORE INTO store_metadata VALUES (?, ?)",
                        (key, expected),
                    )
                    if database.execute(
                        "SELECT value FROM store_metadata WHERE key = ?", (key,)
                    ).fetchone() != (expected,):
                        raise PublicSourceObservationStoreError(
                            "public source store identity mismatch"
                        )
                results = database.execute("SELECT * FROM source_results").fetchall()
                reads = database.execute("SELECT * FROM source_reads").fetchall()
                snapshots = database.execute("SELECT * FROM source_snapshots").fetchall()
        except sqlite3.DatabaseError as exc:
            raise PublicSourceObservationStoreError(
                "public source store is unreadable"
            ) from exc

        for handle, row_json, row_hash in results:
            row = _object(row_json)
            expected_handle = "public-source:" + stable_hash(
                [
                    self.provider,
                    row.get("source_kind"),
                    row.get("source_identity"),
                    self.source_horizon,
                ]
            )[:28]
            if row_hash != stable_hash(row) or handle != expected_handle:
                raise PublicSourceObservationStoreError(
                    "public source result identity mismatch"
                )
            self._results[handle] = row

        for (
            handle,
            revision,
            path,
            metadata_json,
            metadata_hash,
            content,
            content_hash,
        ) in reads:
            metadata = _object(metadata_json)
            result = self._results.get(handle)
            if not (
                metadata_hash == stable_hash(metadata)
                and metadata.get("source_handle") == handle
                and metadata.get("revision") == revision
                and metadata.get("path") == path
                and metadata.get("proof_evidence_status")
                == self.proof_evidence_status
                and result is not None
                and metadata.get("source_identity") == result.get("source_identity")
                and isinstance(content, bytes)
                and len(content) <= self.max_content_bytes
                and hashlib.sha256(content).hexdigest() == content_hash
            ):
                raise PublicSourceObservationStoreError(
                    "public source read identity mismatch"
                )
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise PublicSourceObservationStoreError(
                    "public source content is not UTF-8"
                ) from exc
            stored = {
                field: text if field == "content" else metadata[field]
                for field in _READ_FIELDS
            }
            self._reads[(handle, revision, path)] = stored
            if stored["source_kind"] == "repository":
                self._revisions.setdefault(handle, set()).add(revision)

        for handle, revision, descriptor_json, descriptor_hash in snapshots:
            descriptor = _object(descriptor_json)
            if (
                revision not in self.revisions(handle)
                or stable_hash(descriptor) != descriptor_hash
            ):
                raise PublicSourceObservationStoreError("source snapshot identity mismatch")
            self._snapshots[(handle, revision)] = descriptor


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _object(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PublicSourceObservationStoreError(
            "public source state is not valid JSON"
        ) from exc
    if not isinstance(payload, Mapping):
        raise PublicSourceObservationStoreError(
            "public source state is not an object"
        )
    return dict(payload)

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

try:  # pragma: no cover - unavailable only on non-POSIX hosts
    import resource
except ImportError:  # pragma: no cover
    resource = None

from .fingerprint import stable_hash
from .retrieval import tokens


RESEARCH_SOURCE_SCHEMA_VERSION = 1
RESEARCH_SOURCE_SEARCH_TOOL = "search_research_sources"
RESEARCH_SOURCE_READ_TOOL = "read_research_source"
RESEARCH_SOURCE_RUN_TOOL = "run_research_source"
RESEARCH_SOURCE_NOT_PROOF_EVIDENCE = (
    "RESEARCH_SOURCE_OBSERVATION_NOT_PROOF_EVIDENCE"
)
SOURCE_REPLICATION_NOT_PROOF_EVIDENCE = (
    "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
)
SOURCE_EXECUTION_SCHEMA_VERSION = 1
MAX_SOURCE_FILE_BYTES = 20 * 1024 * 1024
MAX_SOURCE_READ_LINES = 240
MAX_SOURCE_READ_CHARS = 50_000
MAX_SOURCE_SEARCH_HITS = 10
MAX_SOURCE_EXECUTION_OUTPUT_BYTES = 1024 * 1024
PinnedProcessExecutor = Callable[..., Mapping[str, Any]]


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
    manifest_path: Path
    source_root: Path

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

    def document(self, document_id: str) -> ResearchSourceDocument:
        normalized_id = str(document_id or "").strip()
        for document in self.documents:
            if document.document_id == normalized_id:
                return document
        raise ValueError(f"unknown research source document: {normalized_id}")

    def document_path(self, document_id: str) -> Path:
        document = self.document(document_id)
        path = (self.source_root / PurePosixPath(document.relative_path)).resolve()
        try:
            path.relative_to(self.source_root)
        except ValueError as exc:
            raise ValueError("research source document escaped its source root") from exc
        return path

    def identity_errors(self) -> list[str]:
        errors: list[str] = []
        try:
            manifest_hash = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
        except OSError:
            manifest_hash = ""
        if manifest_hash != self.manifest_sha256:
            errors.append("research source manifest changed after snapshot load")
        for document in self.documents:
            path = self.document_path(document.document_id)
            try:
                observed = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                observed = ""
            if observed != document.sha256:
                errors.append(
                    f"research source document changed after snapshot load: "
                    f"{document.document_id}"
                )
        return errors

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
        content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        citation_ref = "research-source-ref:" + stable_hash(
            {
                "snapshot_hash": self.snapshot_hash,
                "document_id": document.document_id,
                "document_sha256": document.sha256,
                "line_start": line_start,
                "line_end": line_end,
                "content_sha256": content_sha256,
            }
        )
        return {
            "ok": True,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            **document.public_descriptor(),
            "line_start": line_start,
            "line_end": line_end,
            "content": content,
            "content_sha256": content_sha256,
            "citation_ref": citation_ref,
            "proof_evidence_status": RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
            "boundary": (
                "This is an exact line-addressed observation from a hash-bound source. "
                "Citation does not establish that the source claim is correct or that "
                "the TheoryDeveloper's use of it is valid."
            ),
        }


@dataclass(frozen=True)
class ResearchSourceExecutionSpec:
    execution_id: str
    benchmark_id: str
    manifest_sha256: str
    source_snapshot_id: str
    source_snapshot_hash: str
    source_manifest_sha256: str
    source_commit: str
    entrypoint_document_id: str
    environment_lock_document_id: str
    environment_root: Path
    python_executable: Path
    python_executable_sha256: str
    runtime_read_roots: tuple[Path, ...]
    working_directory_relative: str
    arguments: tuple[str, ...]
    package_distributions: tuple[tuple[str, str], ...]
    timeout_seconds: int
    max_output_bytes: int
    runtime_executables: tuple[tuple[Path, str], ...] = ()

    def descriptor(self, snapshot: ResearchSourceSnapshot) -> dict[str, Any]:
        entrypoint = snapshot.document(self.entrypoint_document_id)
        environment_lock = snapshot.document(self.environment_lock_document_id)
        return {
            "schema_version": SOURCE_EXECUTION_SCHEMA_VERSION,
            "artifact_kind": "ResearchSourceExecutionDescriptor",
            "execution_id": self.execution_id,
            "benchmark_id": self.benchmark_id,
            "execution_spec_sha256": self.manifest_sha256,
            "source_snapshot_id": self.source_snapshot_id,
            "source_snapshot_hash": self.source_snapshot_hash,
            "source_manifest_sha256": self.source_manifest_sha256,
            "source_commit": self.source_commit,
            "entrypoint_document_id": self.entrypoint_document_id,
            "entrypoint_sha256": entrypoint.sha256,
            "environment_lock_document_id": self.environment_lock_document_id,
            "environment_lock_sha256": environment_lock.sha256,
            "package_distributions": dict(self.package_distributions),
            "timeout_seconds": self.timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
            "runtime_executable_sha256": [
                sha256 for _, sha256 in self.runtime_executables
            ],
            "command_owned_by_model": False,
            "source_mutation_allowed": False,
            "network_access": False,
            "secret_environment_inherited": False,
            "proof_evidence_status": SOURCE_REPLICATION_NOT_PROOF_EVIDENCE,
            "boundary": (
                "The operator fixed the exact interpreter, entrypoint, arguments, "
                "environment, and source hashes before the model session. The model "
                "may inspect sources and request this run, but cannot change the "
                "command. Raw execution is replication evidence, not a theorem proof."
            ),
        }


def load_research_source_execution_spec(
    manifest_path: Path,
    *,
    research_sources: ResearchSourceSnapshot,
) -> ResearchSourceExecutionSpec:
    resolved_manifest = manifest_path.expanduser().resolve()
    manifest_bytes = resolved_manifest.read_bytes()
    payload = json.loads(manifest_bytes.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("research source execution manifest must be a JSON object")
    allowed_fields = {
        "schema_version",
        "artifact_kind",
        "execution_id",
        "benchmark_id",
        "source_snapshot_id",
        "source_snapshot_hash",
        "source_manifest_sha256",
        "source_commit",
        "entrypoint_document_id",
        "environment_lock_document_id",
        "environment_root",
        "python_executable_relative_path",
        "python_executable_sha256",
        "runtime_read_roots",
        "runtime_executables",
        "working_directory_relative",
        "arguments",
        "package_distributions",
        "timeout_seconds",
        "max_output_bytes",
    }
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        raise ValueError(
            "research source execution manifest has unknown fields: "
            + ", ".join(unknown_fields)
        )
    if payload.get("schema_version") != SOURCE_EXECUTION_SCHEMA_VERSION:
        raise ValueError(
            "research source execution schema_version must be "
            f"{SOURCE_EXECUTION_SCHEMA_VERSION}"
        )
    if payload.get("artifact_kind") != "ResearchSourceExecutionSpec":
        raise ValueError(
            "research source execution artifact_kind must be "
            "ResearchSourceExecutionSpec"
        )
    source_snapshot_id = _required_text(payload, "source_snapshot_id")
    source_snapshot_hash = _required_text(payload, "source_snapshot_hash")
    source_manifest_sha256 = _required_text(payload, "source_manifest_sha256")
    if (
        source_snapshot_id != research_sources.snapshot_id
        or source_snapshot_hash != research_sources.snapshot_hash
        or source_manifest_sha256 != research_sources.manifest_sha256
    ):
        raise ValueError(
            "research source execution manifest does not match the configured snapshot"
        )
    entrypoint_document_id = _required_text(payload, "entrypoint_document_id")
    environment_lock_document_id = _required_text(
        payload, "environment_lock_document_id"
    )
    entrypoint = research_sources.document(entrypoint_document_id)
    research_sources.document(environment_lock_document_id)
    if Path(entrypoint.relative_path).suffix.lower() != ".py":
        raise ValueError("research source execution currently requires a Python entrypoint")
    source_commit = _required_text(payload, "source_commit")
    if entrypoint.git_commit and entrypoint.git_commit != source_commit:
        raise ValueError("research source execution commit does not match the entrypoint")

    environment_root = Path(
        _required_text(payload, "environment_root")
    ).expanduser().resolve()
    if not environment_root.is_dir():
        raise ValueError("research source execution environment_root is unavailable")
    executable_relative = PurePosixPath(
        _required_text(payload, "python_executable_relative_path")
    )
    if executable_relative.is_absolute() or ".." in executable_relative.parts:
        raise ValueError("python executable must stay inside environment_root")
    python_executable = environment_root / executable_relative
    resolved_python_executable = python_executable.resolve()
    try:
        python_executable.relative_to(environment_root)
    except ValueError:
        raise ValueError("python executable must stay inside environment_root")
    if not resolved_python_executable.is_file() or not os.access(
        python_executable, os.X_OK
    ):
        raise ValueError("python executable is unavailable or not executable")
    expected_executable_hash = _required_sha256(
        payload, "python_executable_sha256"
    )
    if _file_sha256(resolved_python_executable) != expected_executable_hash:
        raise ValueError("python executable sha256 mismatch")

    raw_runtime_roots = payload.get("runtime_read_roots", [])
    if not isinstance(raw_runtime_roots, list) or len(raw_runtime_roots) > 8:
        raise ValueError("runtime_read_roots must be an array of at most eight paths")
    runtime_roots: list[Path] = []
    for raw_root in raw_runtime_roots:
        if not isinstance(raw_root, str) or not raw_root.strip():
            raise ValueError("runtime_read_roots entries must be nonempty paths")
        root = Path(raw_root).expanduser().resolve()
        if not root.exists():
            raise ValueError(f"runtime read root is unavailable: {root}")
        runtime_roots.append(root)

    raw_runtime_executables = payload.get("runtime_executables", {})
    if not isinstance(raw_runtime_executables, Mapping) or len(
        raw_runtime_executables
    ) > 8:
        raise ValueError(
            "runtime_executables must be an object with at most eight path hashes"
        )
    runtime_executables: list[tuple[Path, str]] = []
    for raw_path, raw_sha256 in raw_runtime_executables.items():
        if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
            raise ValueError("runtime executable paths must be absolute")
        executable_path = Path(raw_path).expanduser().resolve()
        expected_hash = str(raw_sha256 or "").strip().lower()
        if (
            len(expected_hash) != 64
            or any(character not in "0123456789abcdef" for character in expected_hash)
            or not executable_path.is_file()
            or not os.access(executable_path, os.X_OK)
            or _file_sha256(executable_path) != expected_hash
        ):
            raise ValueError(
                f"runtime executable is unavailable or has a sha256 mismatch: "
                f"{executable_path}"
            )
        runtime_executables.append((executable_path, expected_hash))
    runtime_executables.sort(key=lambda row: str(row[0]))

    working_directory_relative = str(
        payload.get("working_directory_relative", ".") or "."
    ).strip()
    working_path = PurePosixPath(working_directory_relative)
    if working_path.is_absolute() or ".." in working_path.parts:
        raise ValueError("working_directory_relative must stay inside source_root")
    working_directory = (research_sources.source_root / working_path).resolve()
    try:
        working_directory.relative_to(research_sources.source_root)
    except ValueError as exc:
        raise ValueError("source execution working directory escaped source_root") from exc
    if not working_directory.is_dir():
        raise ValueError("source execution working directory is unavailable")

    raw_arguments = payload.get("arguments", [])
    if not isinstance(raw_arguments, list) or len(raw_arguments) > 32 or not all(
        isinstance(value, str) and "\x00" not in value for value in raw_arguments
    ):
        raise ValueError("source execution arguments must be at most 32 text values")
    raw_packages = payload.get("package_distributions", {})
    if not isinstance(raw_packages, Mapping) or not raw_packages:
        raise ValueError("package_distributions must be a nonempty object")
    package_distributions: list[tuple[str, str]] = []
    for display_name, distribution_name in raw_packages.items():
        if not all(
            isinstance(value, str) and value.strip()
            for value in (display_name, distribution_name)
        ):
            raise ValueError("package distribution names must be nonempty text")
        package_distributions.append(
            (str(display_name).strip(), str(distribution_name).strip())
        )
    if len(package_distributions) > 64:
        raise ValueError("package_distributions exceeds 64 entries")
    package_distributions.sort()

    timeout_seconds = _bounded_int(
        payload.get("timeout_seconds", 120),
        label="timeout_seconds",
        minimum=1,
        maximum=1800,
    )
    max_output_bytes = _bounded_int(
        payload.get("max_output_bytes", 128 * 1024),
        label="max_output_bytes",
        minimum=1024,
        maximum=MAX_SOURCE_EXECUTION_OUTPUT_BYTES,
    )
    return ResearchSourceExecutionSpec(
        execution_id=_required_text(payload, "execution_id"),
        benchmark_id=_required_text(payload, "benchmark_id"),
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        source_snapshot_id=source_snapshot_id,
        source_snapshot_hash=source_snapshot_hash,
        source_manifest_sha256=source_manifest_sha256,
        source_commit=source_commit,
        entrypoint_document_id=entrypoint_document_id,
        environment_lock_document_id=environment_lock_document_id,
        environment_root=environment_root,
        python_executable=python_executable,
        python_executable_sha256=expected_executable_hash,
        runtime_read_roots=tuple(runtime_roots),
        working_directory_relative=working_directory_relative,
        arguments=tuple(raw_arguments),
        package_distributions=tuple(package_distributions),
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
        runtime_executables=tuple(runtime_executables),
    )


def execute_research_source(
    *,
    execution: ResearchSourceExecutionSpec,
    research_sources: ResearchSourceSnapshot,
    output_dir: Path,
    question_id: str,
    process_executor: PinnedProcessExecutor | None = None,
) -> dict[str, Any]:
    """Execute one operator-bound author entrypoint without model-owned commands."""

    if not str(question_id or "").strip():
        raise ValueError("source replication requires question identity")
    if (
        execution.source_snapshot_id != research_sources.snapshot_id
        or execution.source_snapshot_hash != research_sources.snapshot_hash
        or execution.source_manifest_sha256 != research_sources.manifest_sha256
    ):
        raise ValueError("source execution spec is not bound to this source snapshot")
    resolved_output = output_dir.expanduser().resolve()
    resolved_output.mkdir(parents=True, exist_ok=False)
    entrypoint = research_sources.document(execution.entrypoint_document_id)
    entrypoint_path = research_sources.document_path(entrypoint.document_id)
    environment_lock = research_sources.document(
        execution.environment_lock_document_id
    )
    working_directory = (
        research_sources.source_root
        / PurePosixPath(execution.working_directory_relative)
    ).resolve()
    executor = process_executor or _execute_pinned_process
    pre_identity_errors = research_sources.identity_errors()
    errors = list(pre_identity_errors)
    if _file_sha256(execution.python_executable) != execution.python_executable_sha256:
        errors.append("python executable changed after execution-spec load")
    for executable_path, expected_hash in execution.runtime_executables:
        if _file_sha256(executable_path) != expected_hash:
            errors.append("runtime executable changed after execution-spec load")

    package_probe_path = resolved_output / "environment_probe.py"
    package_probe_code = _python_environment_probe_code(
        dict(execution.package_distributions)
    )
    package_probe_path.write_text(package_probe_code, encoding="utf-8")
    probe_result: dict[str, Any] = {
        "execution_attempted": False,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "errors": [],
    }
    source_result: dict[str, Any] = {
        "execution_attempted": False,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "errors": [],
    }
    common_executor_inputs = {
        "environment_root": execution.environment_root,
        "runtime_read_roots": execution.runtime_read_roots,
        "runtime_executables": execution.runtime_executables,
        "source_paths": tuple(
            research_sources.document_path(document.document_id)
            for document in research_sources.documents
        ),
        "output_dir": resolved_output,
        "timeout_seconds": execution.timeout_seconds,
        "max_output_bytes": execution.max_output_bytes,
    }
    if not errors:
        probe_result = dict(
            executor(
                command=(
                    str(execution.python_executable),
                    str(package_probe_path),
                ),
                cwd=resolved_output,
                stdout_path=resolved_output / "environment_probe.stdout",
                stderr_path=resolved_output / "environment_probe.stderr",
                **common_executor_inputs,
            )
        )
        errors.extend(str(value) for value in probe_result.get("errors", []) or [])
    probe_payload: dict[str, Any] = {}
    if not errors and probe_result.get("returncode") == 0:
        try:
            raw_probe = json.loads(str(probe_result.get("stdout", "") or ""))
            probe_payload = dict(raw_probe) if isinstance(raw_probe, Mapping) else {}
        except json.JSONDecodeError:
            errors.append("source environment probe did not return a JSON object")
        if not str(probe_payload.get("python_version", "") or "").strip():
            errors.append("source environment probe omitted python_version")
        observed_packages = probe_payload.get("package_versions", {})
        if not isinstance(observed_packages, Mapping) or set(observed_packages) != set(
            dict(execution.package_distributions)
        ):
            errors.append("source environment probe package identity is incomplete")
    elif probe_result.get("execution_attempted"):
        errors.append("source environment probe failed")

    if not errors:
        source_result = dict(
            executor(
                command=(
                    str(execution.python_executable),
                    str(entrypoint_path),
                    *execution.arguments,
                ),
                cwd=working_directory,
                stdout_path=resolved_output / "source.stdout",
                stderr_path=resolved_output / "source.stderr",
                **common_executor_inputs,
            )
        )
        errors.extend(str(value) for value in source_result.get("errors", []) or [])
        if source_result.get("returncode") != 0:
            errors.append(
                "pinned research source exited "
                + str(source_result.get("returncode"))
            )

    post_identity_errors = research_sources.identity_errors()
    source_mutated = bool(pre_identity_errors or post_identity_errors)
    errors.extend(post_identity_errors)
    if _file_sha256(execution.python_executable) != execution.python_executable_sha256:
        errors.append("python executable changed during source execution")
    for executable_path, expected_hash in execution.runtime_executables:
        if _file_sha256(executable_path) != expected_hash:
            errors.append("runtime executable changed during source execution")
    errors = list(dict.fromkeys(value for value in errors if value))
    raw_stdout = str(source_result.get("stdout", "") or "")
    raw_stderr = str(source_result.get("stderr", "") or "")
    stdout_sha256 = hashlib.sha256(raw_stdout.encode("utf-8")).hexdigest()
    stderr_sha256 = hashlib.sha256(raw_stderr.encode("utf-8")).hexdigest()
    artifact_id = "source_replication:" + stable_hash(
        [
            question_id,
            execution.execution_id,
            research_sources.snapshot_hash,
            entrypoint.sha256,
            stdout_sha256,
            source_result.get("returncode"),
        ]
    )[:20]
    manifest_path = resolved_output / "source_replication_manifest.json"
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": artifact_id,
        "question_id": str(question_id),
        "benchmark_id": execution.benchmark_id,
        "execution_id": execution.execution_id,
        "execution_spec_sha256": execution.manifest_sha256,
        "source_snapshot_id": research_sources.snapshot_id,
        "source_snapshot_hash": research_sources.snapshot_hash,
        "source_manifest_sha256": research_sources.manifest_sha256,
        "source_commit": execution.source_commit,
        "entrypoint_document_id": entrypoint.document_id,
        "executed_entrypoint_sha256": entrypoint.sha256,
        "environment_lock_document_id": environment_lock.document_id,
        "environment_lock_sha256": environment_lock.sha256,
        "python_executable_sha256": execution.python_executable_sha256,
        "runtime_executable_sha256": [
            sha256 for _, sha256 in execution.runtime_executables
        ],
        "environment_probe_sha256": hashlib.sha256(
            package_probe_code.encode("utf-8")
        ).hexdigest(),
        "python_version": str(probe_payload.get("python_version", "") or ""),
        "package_versions": dict(probe_payload.get("package_versions", {}) or {}),
        "execution_attempted": source_result.get("execution_attempted") is True,
        "returncode": source_result.get("returncode"),
        "errors": errors,
        "raw_stdout": raw_stdout,
        "raw_stderr": raw_stderr,
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
        "source_mutated": source_mutated,
        "runtime_edited_source": False,
        "command_owned_by_model": False,
        "network_access": False,
        "secret_environment_inherited": False,
        "execution_status": "EXECUTED" if not errors else "FAILED",
        "manifest_path": str(manifest_path),
        "runtime_generated": True,
        "model_authored": False,
        "proof_evidence_status": SOURCE_REPLICATION_NOT_PROOF_EVIDENCE,
        "kernel_verified": False,
        "boundary": (
            "This manifest records an exact immutable author-source rerun and raw "
            "environment feedback. It does not validate a rewritten implementation, "
            "establish a statistical theorem, or count as Lean proof evidence."
        ),
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _python_environment_probe_code(package_distributions: Mapping[str, str]) -> str:
    mapping_json = json.dumps(
        dict(sorted(package_distributions.items())),
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return (
        "import importlib.metadata as metadata\n"
        "import json\n"
        "import platform\n"
        f"distributions = {mapping_json}\n"
        "payload = {\n"
        "    'python_version': platform.python_version(),\n"
        "    'package_versions': {\n"
        "        label: metadata.version(distribution)\n"
        "        for label, distribution in distributions.items()\n"
        "    },\n"
        "}\n"
        "print(json.dumps(payload, sort_keys=True, separators=(',', ':')))\n"
    )


def _execute_pinned_process(
    *,
    command: Sequence[str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    environment_root: Path,
    runtime_read_roots: Sequence[Path],
    runtime_executables: Sequence[tuple[Path, str]],
    source_paths: Sequence[Path],
    output_dir: Path,
    timeout_seconds: int,
    max_output_bytes: int,
) -> Mapping[str, Any]:
    sandbox_executable = shutil.which("sandbox-exec") if sys.platform == "darwin" else None
    if not sandbox_executable:
        return {
            "execution_attempted": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "errors": ["sandbox-exec is required for immutable source execution"],
        }
    requested_executable = Path(command[0]).expanduser().absolute()
    exact_executable = requested_executable.resolve()
    profile = _source_execution_sandbox_profile(
        requested_executable=requested_executable,
        executable=exact_executable,
        environment_root=environment_root,
        runtime_read_roots=runtime_read_roots,
        runtime_executables=runtime_executables,
        source_paths=source_paths,
        output_dir=output_dir,
    )
    sandbox_command = [sandbox_executable, "-p", profile, *command]
    environment = {
        "HOME": str(output_dir),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": str(environment_root / "bin"),
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TMPDIR": str(output_dir),
        "TZ": "UTC",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    }
    limits = {
        "cpu_seconds": max(2, int(math.ceil(timeout_seconds)) + 1),
        "file_size_bytes": max_output_bytes,
        "open_files": 128,
    }
    returncode: int | None = None
    transport_errors: list[str] = []
    try:
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            completed = subprocess.run(
                sandbox_command,
                cwd=str(cwd),
                env=environment,
                check=False,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=timeout_seconds,
                preexec_fn=_source_execution_resource_limiter(limits),
            )
        returncode = int(completed.returncode)
    except subprocess.TimeoutExpired:
        returncode = 124
        transport_errors.append(f"source execution timed out after {timeout_seconds}s")
    except Exception as exc:  # pragma: no cover - defensive transport failure
        returncode = 125
        transport_errors.append(f"source execution transport failed: {type(exc).__name__}")
    stdout, stdout_errors = _bounded_execution_text(stdout_path, max_output_bytes)
    stderr, stderr_errors = _bounded_execution_text(stderr_path, max_output_bytes)
    transport_errors.extend(stdout_errors)
    transport_errors.extend(stderr_errors)
    return {
        "execution_attempted": True,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "errors": transport_errors,
    }


def _source_execution_resource_limiter(limits: Mapping[str, int]):
    def apply_limits() -> None:
        if resource is None:  # pragma: no cover
            return
        os.setsid()
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (limits["cpu_seconds"], limits["cpu_seconds"]),
        )
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (limits["file_size_bytes"], limits["file_size_bytes"]),
        )
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (limits["open_files"], limits["open_files"]),
        )

    return apply_limits


def _source_execution_sandbox_profile(
    *,
    requested_executable: Path,
    executable: Path,
    environment_root: Path,
    runtime_read_roots: Sequence[Path],
    runtime_executables: Sequence[tuple[Path, str]],
    source_paths: Sequence[Path],
    output_dir: Path,
) -> str:
    read_subpaths = {
        "/Library/Apple/System/Library",
        "/System",
        "/private/var/db/timezone",
        "/usr/lib",
        "/usr/share",
        _seatbelt_path(environment_root),
        _seatbelt_path(output_dir),
        *(_seatbelt_path(path) for path in runtime_read_roots),
    }
    read_literals = {
        "/",
        "/dev/null",
        "/dev/random",
        "/dev/urandom",
        "/etc/localtime",
        _seatbelt_path(executable),
        *(_seatbelt_path(path) for path in source_paths),
    }
    process_literals = {
        *(
            _seatbelt_literal_path(path)
            for path in _executable_symlink_chain(requested_executable)
        ),
        _seatbelt_path(executable),
        *(
            _seatbelt_literal_path(path)
            for executable_path, _ in runtime_executables
            for path in _executable_symlink_chain(executable_path)
        ),
    }
    read_rules = " ".join(
        f'(subpath "{path}")' for path in sorted(read_subpaths)
    ) + " " + " ".join(
        f'(literal "{path}")' for path in sorted(read_literals)
    )
    metadata_literals = {"/etc", "/tmp", "/var"}
    for raw_path in read_subpaths | read_literals | {_seatbelt_path(output_dir)}:
        metadata_literals.update(str(parent) for parent in Path(raw_path).parents)
    metadata_rules = " ".join(
        f'(literal "{path.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}")'
        for path in sorted(metadata_literals)
    )
    process_rules = " ".join(
        f'(literal "{path}")' for path in sorted(process_literals)
    )
    return (
        "(version 1) (allow default) "
        "(deny network*) "
        "(deny process-fork) "
        "(deny process-exec) "
        f"(allow process-exec {process_rules}) "
        "(deny file-read*) "
        f"(allow file-read* {read_rules}) "
        f"(allow file-read-metadata {metadata_rules}) "
        "(deny file-write*) "
        f'(allow file-write* (subpath "{_seatbelt_path(output_dir)}"))'
    )


def _seatbelt_path(path: Path) -> str:
    return str(path.expanduser().resolve()).replace("\\", "\\\\").replace(
        '"', '\\"'
    )


def _seatbelt_literal_path(path: Path) -> str:
    return str(path.expanduser().absolute()).replace("\\", "\\\\").replace(
        '"', '\\"'
    )


def _executable_symlink_chain(path: Path) -> tuple[Path, ...]:
    current = path.expanduser().absolute()
    chain: list[Path] = []
    for _ in range(16):
        chain.append(current)
        if not current.is_symlink():
            break
        target = Path(os.readlink(current))
        current = target if target.is_absolute() else current.parent / target
        current = current.absolute()
    resolved = path.expanduser().resolve()
    if resolved not in chain:
        chain.append(resolved)
    return tuple(chain)


def _bounded_execution_text(path: Path, max_output_bytes: int) -> tuple[str, list[str]]:
    if not path.exists():
        return "", []
    raw = path.read_bytes()
    errors: list[str] = []
    if len(raw) > max_output_bytes:
        raw = raw[:max_output_bytes]
        errors.append(f"source execution output exceeded {max_output_bytes} bytes")
    return raw.decode("utf-8", errors="replace"), errors


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
        manifest_path=resolved_manifest,
        source_root=source_root,
    )


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"research source manifest field {field} must be nonempty text")
    return value.strip()


def _required_sha256(payload: Mapping[str, Any], field: str) -> str:
    value = _required_text(payload, field).lower()
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _bounded_int(
    value: Any,
    *,
    label: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}")
    return value

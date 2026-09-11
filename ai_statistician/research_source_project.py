from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .fingerprint import stable_hash
from .research_source_library import (
    MAX_SOURCE_FILE_BYTES,
    ResearchSourceSnapshot,
    load_research_source_snapshot,
    normalized_internal_symlink_destination,
)


MAX_REPOSITORY_SNAPSHOT_FILES = 20_000
MAX_REPOSITORY_SNAPSHOT_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_PUBLIC_GITHUB_FETCH_TIMEOUT_SECONDS = 300
_GIT_BLOB_FILE_MODES = frozenset({"100644", "100755", "120000"})
_GITHUB_REPOSITORY_PART = re.compile(r"[0-9A-Za-z_.-]+")


def _local_git_environment() -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_ALLOW_PROTOCOL": "",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PROTOCOL_FROM_USER": "0",
        "GIT_TERMINAL_PROMPT": "0",
    }
    for name in ("SYSTEMROOT", "TEMP", "TMP", "TMPDIR"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


def _validated_snapshot_request(
    *,
    output_dir: Path,
    snapshot_id: str,
    source_horizon: str,
    max_files: int,
    max_total_bytes: int,
) -> tuple[Path, str, date]:
    destination = output_dir.expanduser().resolve()
    normalized_snapshot_id = str(snapshot_id or "").strip()
    if not normalized_snapshot_id or len(normalized_snapshot_id) > 200:
        raise ValueError("snapshot_id must be nonempty and bounded")
    try:
        horizon_date = date.fromisoformat(str(source_horizon or "").strip())
    except ValueError as exc:
        raise ValueError("source_horizon must be an ISO date") from exc
    if (
        isinstance(max_files, bool)
        or not isinstance(max_files, int)
        or not 1 <= max_files <= 100_000
    ):
        raise ValueError("max_files must be between 1 and 100000")
    if (
        isinstance(max_total_bytes, bool)
        or not isinstance(max_total_bytes, int)
        or not MAX_SOURCE_FILE_BYTES <= max_total_bytes <= 16 * 1024**3
    ):
        raise ValueError("max_total_bytes is outside the supported boundary")
    if destination.exists():
        raise ValueError("output_dir already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination, normalized_snapshot_id, horizon_date


def acquire_public_github_repository_snapshot(
    *,
    repository_url: str,
    revision: str,
    output_dir: Path,
    snapshot_id: str,
    source_horizon: str,
    license_name: str = "",
    max_files: int = MAX_REPOSITORY_SNAPSHOT_FILES,
    max_total_bytes: int = MAX_REPOSITORY_SNAPSHOT_BYTES,
    fetch_timeout_seconds: int = DEFAULT_PUBLIC_GITHUB_FETCH_TIMEOUT_SECONDS,
) -> ResearchSourceSnapshot:
    """Fetch one exact public GitHub commit, then freeze it without network."""

    canonical_url = _canonical_public_github_repository_url(repository_url)
    normalized_revision = str(revision or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", normalized_revision):
        raise ValueError("public GitHub revision must be one full SHA-1 commit")
    if (
        isinstance(fetch_timeout_seconds, bool)
        or not isinstance(fetch_timeout_seconds, int)
        or not 1 <= fetch_timeout_seconds <= 3_600
    ):
        raise ValueError("fetch_timeout_seconds must be between 1 and 3600")
    destination, normalized_snapshot_id, _ = _validated_snapshot_request(
        output_dir=output_dir,
        snapshot_id=snapshot_id,
        source_horizon=source_horizon,
        max_files=max_files,
        max_total_bytes=max_total_bytes,
    )

    stage = Path(
        tempfile.mkdtemp(
            prefix=".research-source-acquisition-",
            dir=destination.parent,
        )
    )
    try:
        repository = stage / "repository"
        repository.mkdir()
        private_home = stage / "home"
        private_home.mkdir()
        _run_public_git(
            ["git", "-C", str(repository), "init", "--quiet"],
            private_home=private_home,
            timeout_seconds=fetch_timeout_seconds,
        )
        _run_public_git(
            [
                "git",
                "-C",
                str(repository),
                "-c",
                "fetch.unpackLimit=1",
                "-c",
                "http.followRedirects=false",
                "fetch",
                "--quiet",
                "--no-tags",
                "--depth=1",
                f"--filter=blob:limit={MAX_SOURCE_FILE_BYTES + 1}",
                canonical_url + ".git",
                normalized_revision,
            ],
            private_home=private_home,
            timeout_seconds=fetch_timeout_seconds,
        )
        observed_commit = _git_text(
            repository,
            "rev-parse",
            "--verify",
            "--end-of-options",
            "FETCH_HEAD^{commit}",
        ).lower()
        if observed_commit != normalized_revision:
            raise ValueError("public GitHub fetch returned a different commit")
        return freeze_git_repository_snapshot(
            repository_root=repository,
            revision=observed_commit,
            output_dir=destination,
            snapshot_id=normalized_snapshot_id,
            source_horizon=source_horizon,
            repository_url=canonical_url,
            license_name=license_name,
            max_files=max_files,
            max_total_bytes=max_total_bytes,
        )
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _canonical_public_github_repository_url(value: str) -> str:
    normalized = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(normalized)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("public repository URL is invalid") from exc
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or len(parts) != 3
        or parts[0]
        or any(not _GITHUB_REPOSITORY_PART.fullmatch(part) for part in parts[1:])
        or urllib.parse.unquote(path) != path
    ):
        raise ValueError(
            "public repository URL must be https://github.com/owner/repository"
        )
    return "https://github.com/" + "/".join(parts[1:])


def _run_public_git(
    command: list[str],
    *,
    private_home: Path,
    timeout_seconds: int,
) -> None:
    environment = _local_git_environment()
    environment.update({
        "GIT_ALLOW_PROTOCOL": "https",
        "HOME": str(private_home),
        "XDG_CONFIG_HOME": str(private_home / ".config"),
    })
    environment.pop("GIT_NO_LAZY_FETCH", None)
    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            timeout=timeout_seconds,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        streams = [
            value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value or "")
            for value in (exc.stdout, exc.stderr)
        ]
        raise ValueError(
            f"public GitHub repository acquisition failed: {exc}\n"
            f"stdout:\n{streams[0]}\nstderr:\n{streams[1]}"
        ) from exc
    except OSError as exc:
        raise ValueError(f"public GitHub repository acquisition failed: {exc}") from exc


def freeze_git_repository_snapshot(
    *,
    repository_root: Path,
    revision: str,
    output_dir: Path,
    snapshot_id: str,
    source_horizon: str,
    repository_url: str = "",
    license_name: str = "",
    max_files: int = MAX_REPOSITORY_SNAPSHOT_FILES,
    max_total_bytes: int = MAX_REPOSITORY_SNAPSHOT_BYTES,
) -> ResearchSourceSnapshot:
    """Freeze one exact local Git commit as a source-replication project."""

    repository = repository_root.expanduser().resolve()
    normalized_revision = str(revision or "").strip()
    if not repository.is_dir():
        raise ValueError("repository_root must be an existing directory")
    if (
        not normalized_revision
        or normalized_revision.startswith("-")
        or len(normalized_revision) > 200
        or not re.fullmatch(r"[0-9A-Za-z._/@+-]+", normalized_revision)
    ):
        raise ValueError("revision must be one bounded Git revision without options")
    destination, normalized_snapshot_id, horizon_date = _validated_snapshot_request(
        output_dir=output_dir,
        snapshot_id=snapshot_id,
        source_horizon=source_horizon,
        max_files=max_files,
        max_total_bytes=max_total_bytes,
    )

    top_level = Path(
        _git_text(repository, "rev-parse", "--show-toplevel")
    ).resolve()
    if top_level != repository:
        raise ValueError("repository_root must be the Git worktree root")
    object_format = _git_text(
        repository, "rev-parse", "--show-object-format"
    ).lower()
    if object_format not in {"sha1", "sha256"}:
        raise ValueError("Git repository object format is unsupported")
    commit = _git_text(
        repository,
        "rev-parse",
        "--verify",
        "--end-of-options",
        normalized_revision + "^{commit}",
    ).lower()
    expected_oid_length = 40 if object_format == "sha1" else 64
    if len(commit) != expected_oid_length or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise ValueError("revision did not resolve to one full commit identity")
    commit_dates = _git_text(
        repository, "show", "-s", "--format=%aI%n%cI", commit
    ).splitlines()
    if len(commit_dates) != 2:
        raise ValueError("Git commit did not expose author and committer dates")
    try:
        author_date, committer_date = (
            datetime.fromisoformat(value).date() for value in commit_dates
        )
    except ValueError as exc:
        raise ValueError("Git commit dates are invalid") from exc
    if author_date > horizon_date or committer_date > horizon_date:
        raise ValueError("Git commit falls after the configured source horizon")

    tree_rows = _git_tree_rows(repository, commit)
    if not tree_rows:
        raise ValueError("Git commit contains no supported tracked files")
    if len(tree_rows) > max_files:
        raise ValueError("Git commit exceeds the configured file-count boundary")
    total_bytes = sum(int(row["byte_size"]) for row in tree_rows)
    if total_bytes > max_total_bytes:
        raise ValueError("Git commit exceeds the configured aggregate byte boundary")

    stage = Path(
        tempfile.mkdtemp(prefix=".research-source-project-", dir=destination.parent)
    )
    try:
        source_root = stage / "repository"
        source_root.mkdir()
        documents = _materialize_git_blobs(
            repository=repository,
            source_root=source_root,
            tree_rows=tree_rows,
            object_format=object_format,
            commit=commit,
            repository_url=str(repository_url or "").strip(),
            license_name=str(license_name or "").strip(),
        )
        manifest = {
            "schema_version": 1,
            "snapshot_id": normalized_snapshot_id,
            "source_horizon": str(source_horizon).strip(),
            "source_root": "repository",
            "repository_identity": {
                "repository_url": str(repository_url or "").strip(),
                "git_commit": commit,
                "git_object_format": object_format,
                "author_date": commit_dates[0],
                "committer_date": commit_dates[1],
                "tracked_file_count": len(documents),
                "tracked_byte_size": total_bytes,
                "tree_index_hash": stable_hash([
                    {
                        "relative_path": row["relative_path"],
                        "git_blob_oid": row["git_blob_oid"],
                        "file_mode": row["file_mode"],
                        "byte_size": row["byte_size"],
                    }
                    for row in documents
                ]),
            },
            "documents": documents,
        }
        (stage / "sources.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validated_snapshot = load_research_source_snapshot(stage / "sources.json")
        published_snapshot = replace(
            validated_snapshot,
            manifest_path=destination / "sources.json",
            source_root=destination / "repository",
        )
        os.replace(stage, destination)
        return published_snapshot
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _git_tree_rows(repository: Path, commit: str) -> list[dict[str, Any]]:
    raw = _run_git(
        repository,
        "ls-tree",
        "-r",
        "-z",
        "-l",
        "--full-tree",
        commit,
        text=False,
    )
    rows = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            header, raw_path = record.split(b"\t", 1)
            mode, object_type, oid, raw_size = header.decode("ascii").split()
            relative_path = raw_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("Git tree contains an unsupported path or row") from exc
        path = PurePosixPath(relative_path)
        if (
            path.is_absolute()
            or any(part in {"", ".", ".."} for part in path.parts)
            or path.as_posix() != relative_path
        ):
            raise ValueError("Git tree contains a non-canonical path")
        if object_type != "blob" or mode not in _GIT_BLOB_FILE_MODES:
            raise ValueError(
                "Git snapshot supports regular files and internal file symlinks; "
                f"submodules and other tree entries are unsupported: {relative_path}"
            )
        try:
            byte_size = int(raw_size)
        except ValueError as exc:
            raise ValueError(
                "Git snapshot requires every tracked blob to be available locally: "
                + relative_path
            ) from exc
        if byte_size > MAX_SOURCE_FILE_BYTES:
            raise ValueError(
                f"Git tracked file exceeds {MAX_SOURCE_FILE_BYTES} bytes: {relative_path}"
            )
        rows.append({
            "relative_path": relative_path,
            "file_mode": mode,
            "git_blob_oid": oid.lower(),
            "byte_size": byte_size,
        })
    return sorted(rows, key=lambda row: str(row["relative_path"]))


def _materialize_git_blobs(
    *,
    repository: Path,
    source_root: Path,
    tree_rows: list[Mapping[str, Any]],
    object_format: str,
    commit: str,
    repository_url: str,
    license_name: str,
) -> list[dict[str, Any]]:
    documents = []
    tree_modes = {
        str(row["relative_path"]): str(row["file_mode"])
        for row in tree_rows
    }
    pending_symlinks: list[tuple[Path, str, str]] = []
    process = subprocess.Popen(
        ["git", "-C", str(repository), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_local_git_environment(),
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        raise ValueError("Git blob reader did not expose its process streams")
    try:
        for tree_row in tree_rows:
            relative_path = str(tree_row["relative_path"])
            expected_oid = str(tree_row["git_blob_oid"])
            process.stdin.write((expected_oid + "\n").encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii", errors="strict").strip()
            try:
                observed_oid, object_type, raw_size = header.split()
                byte_size = int(raw_size)
            except ValueError as exc:
                raise ValueError(
                    f"Git blob reader returned an invalid header: {relative_path}"
                ) from exc
            if (
                observed_oid != expected_oid
                or object_type != "blob"
                or byte_size != int(tree_row["byte_size"])
            ):
                raise ValueError(f"Git blob metadata mismatch: {relative_path}")
            raw_bytes = process.stdout.read(byte_size)
            terminator = process.stdout.read(1)
            if len(raw_bytes) != byte_size or terminator != b"\n":
                raise ValueError(f"Git blob was truncated: {relative_path}")
            observed_oid = _git_blob_oid(raw_bytes, algorithm=object_format)
            if observed_oid != expected_oid:
                raise ValueError(f"Git blob identity mismatch: {relative_path}")
            target = source_root / PurePosixPath(relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            symlink_target = ""
            if tree_row["file_mode"] == "120000":
                try:
                    symlink_target = raw_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError(
                        f"Git symlink target is not UTF-8: {relative_path}"
                    ) from exc
                destination = normalized_internal_symlink_destination(
                    link_path=relative_path,
                    target=symlink_target,
                )
                if tree_modes.get(destination) not in {"100644", "100755"}:
                    raise ValueError(
                        "Git symlink must target one regular tracked file: "
                        + relative_path
                    )
                pending_symlinks.append((target, symlink_target, destination))
                content_mode = "text"
                media_type = "inode/symlink"
            else:
                target.write_bytes(raw_bytes)
                target.chmod(
                    0o755 if tree_row["file_mode"] == "100755" else 0o644
                )
                try:
                    decoded = raw_bytes.decode("utf-8")
                    content_mode = "text" if "\x00" not in decoded else "binary"
                except UnicodeDecodeError:
                    content_mode = "binary"
                guessed_media = mimetypes.guess_type(relative_path)[0]
                media_type = guessed_media or (
                    "text/plain"
                    if content_mode == "text"
                    else "application/octet-stream"
                )
            quoted_path = "/".join(
                urllib.parse.quote(part, safe="")
                for part in PurePosixPath(relative_path).parts
            )
            documents.append({
                "document_id": "repository-file:"
                + stable_hash([commit, relative_path])[:24],
                "title": relative_path,
                "source_kind": (
                    "repository_symlink"
                    if symlink_target
                    else (
                        "repository_text"
                        if content_mode == "text"
                        else "repository_asset"
                    )
                ),
                "relative_path": relative_path,
                "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "byte_size": len(raw_bytes),
                "content_mode": content_mode,
                "media_type": media_type,
                "file_mode": str(tree_row["file_mode"]),
                "git_blob_oid": str(tree_row["git_blob_oid"]),
                "git_commit": commit,
                "model_visible": True,
                "url": (
                    repository_url.rstrip("/") + f"/blob/{commit}/" + quoted_path
                    if repository_url
                    else ""
                ),
                "license": license_name,
                **(
                    {"symlink_target": symlink_target}
                    if symlink_target
                    else {}
                ),
            })
        process.stdin.close()
        returncode = process.wait(timeout=30)
        stderr = process.stderr.read().decode("utf-8", errors="replace").strip()
        if returncode != 0:
            raise ValueError("Git blob reader failed" + (": " + stderr if stderr else ""))
        for target, symlink_target, destination in pending_symlinks:
            resolved_destination = source_root / PurePosixPath(destination)
            if not resolved_destination.is_file() or resolved_destination.is_symlink():
                raise ValueError(
                    "Git symlink target was not materialized as a regular file: "
                    + target.relative_to(source_root).as_posix()
                )
            target.symlink_to(symlink_target)
            if target.resolve(strict=True) != resolved_destination.resolve(strict=True):
                raise ValueError(
                    "Git symlink resolved to an unexpected destination: "
                    + target.relative_to(source_root).as_posix()
                )
    except Exception:
        if process.poll() is None:
            process.kill()
            process.wait()
        raise
    return documents


def _git_blob_oid(raw_bytes: bytes, *, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    digest.update(f"blob {len(raw_bytes)}\0".encode("ascii"))
    digest.update(raw_bytes)
    return digest.hexdigest()


def _git_text(repository: Path, *arguments: str) -> str:
    return str(_run_git(repository, *arguments, text=True)).strip()


def _run_git(
    repository: Path,
    *arguments: str,
    text: bool = True,
) -> str | bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
            env=_local_git_environment(),
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("Git project snapshot command failed") from exc
    return result.stdout

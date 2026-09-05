from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash
from .lean_candidate_identity import run_lean_candidate_identity_probe


LEAN_PROJECT_ARTIFACT_KIND = "ModelAuthoredLeanProject"
LEAN_PROJECT_REFERENCE_KIND = "ModelAuthoredLeanProjectRef"
LEAN_PROJECT_REFERENCE_DIRECTORY = ".model_authored_lean_projects"
LEAN_PROJECT_MAIN_PATH = "Main.lean"
MAX_LEAN_PROJECT_SUPPORT_FILES = 64
MAX_LEAN_PROJECT_FILE_BYTES = 512 * 1024
MAX_LEAN_PROJECT_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class LeanProjectFile:
    path: str
    content: str
    content_sha256: str

    def to_json(self) -> dict[str, str]:
        return {
            "path": self.path,
            "content": self.content,
            "content_sha256": self.content_sha256,
        }


def _lean_project_path_error(path: str) -> str:
    pure = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or "\x00" in path
        or pure.is_absolute()
        or path != pure.as_posix()
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        return f"Lean project path is not canonical and relative: {path!r}"
    if path.casefold() == LEAN_PROJECT_MAIN_PATH.casefold():
        return f"Lean support file collides with {LEAN_PROJECT_MAIN_PATH}"
    if pure.suffix != ".lean":
        return f"Lean project support file must end in .lean: {path}"
    return ""


def lean_project_file_errors(value: Any) -> list[str]:
    if value in (None, ()):
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ["Lean project support_files must be an array"]
    if len(value) > MAX_LEAN_PROJECT_SUPPORT_FILES:
        return [
            f"Lean project exceeds {MAX_LEAN_PROJECT_SUPPORT_FILES} support files"
        ]
    errors: list[str] = []
    paths: set[str] = set()
    total_bytes = 0
    for index, raw in enumerate(value):
        if isinstance(raw, LeanProjectFile):
            path, content = raw.path, raw.content
            supplied_sha256 = raw.content_sha256
        elif isinstance(raw, Mapping):
            unexpected = set(raw) - {"path", "content", "content_sha256"}
            if unexpected:
                errors.append(
                    f"Lean project file {index} has unexpected fields: "
                    + ", ".join(sorted(unexpected))
                )
            path, content = raw.get("path"), raw.get("content")
            supplied_sha256 = raw.get("content_sha256", "")
        else:
            errors.append(f"Lean project file {index} must be an object")
            continue
        if not isinstance(path, str) or not isinstance(content, str):
            errors.append(
                f"Lean project file {index} requires text path and content"
            )
            continue
        path_error = _lean_project_path_error(path)
        if path_error:
            errors.append(path_error)
        path_identity = path.casefold()
        if path_identity in paths:
            errors.append(f"duplicate Lean project path: {path}")
        paths.add(path_identity)
        encoded = content.encode("utf-8")
        total_bytes += len(encoded)
        if not content.strip():
            errors.append(f"Lean project file is empty: {path}")
        if len(encoded) > MAX_LEAN_PROJECT_FILE_BYTES:
            errors.append(f"Lean project file exceeds size boundary: {path}")
        observed_sha256 = hashlib.sha256(encoded).hexdigest()
        if supplied_sha256 and supplied_sha256 != observed_sha256:
            errors.append(f"Lean project file hash mismatch: {path}")
    if total_bytes > MAX_LEAN_PROJECT_BYTES:
        errors.append("Lean project support files exceed aggregate size boundary")
    return sorted(set(errors))


def normalized_lean_project_files(value: Any) -> tuple[LeanProjectFile, ...]:
    rows = [] if value in (None, ()) else value
    errors = lean_project_file_errors(rows)
    if errors:
        raise ValueError("; ".join(errors))
    normalized: list[LeanProjectFile] = []
    for raw in rows:
        path = raw.path if isinstance(raw, LeanProjectFile) else str(raw["path"])
        content = (
            raw.content if isinstance(raw, LeanProjectFile) else str(raw["content"])
        )
        normalized.append(
            LeanProjectFile(
                path=path,
                content=content,
                content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(sorted(normalized, key=lambda row: row.path))


def lean_project_build_order_errors(
    build_order: Any,
    *,
    project_files: Sequence[LeanProjectFile],
    require_complete: bool = True,
) -> list[str]:
    if not isinstance(build_order, Sequence) or isinstance(
        build_order, (str, bytes)
    ):
        return ["Lean project support_build_order must be an array"]
    if any(not isinstance(value, str) or not value for value in build_order):
        return ["Lean project support_build_order must contain nonempty paths"]
    observed = list(build_order)
    if len(observed) != len(set(observed)):
        return ["Lean project support_build_order contains duplicate paths"]
    known = {row.path for row in project_files}
    unknown = [path for path in observed if path not in known]
    errors = (
        ["Lean project support_build_order has unknown paths: " + ", ".join(unknown)]
        if unknown
        else []
    )
    if require_complete and set(observed) != known:
        errors.append(
            "Lean project support_build_order must contain every support file exactly once"
        )
    return errors


def lean_project_hash(
    *,
    target_source: str,
    project_files: Any = (),
    support_build_order: Sequence[str] = (),
) -> str:
    rows = normalized_lean_project_files(project_files)
    errors = lean_project_build_order_errors(
        support_build_order,
        project_files=rows,
        require_complete=True,
    )
    if errors:
        raise ValueError("; ".join(errors))
    return stable_hash(
        {
            "main": {
                "path": LEAN_PROJECT_MAIN_PATH,
                "source_hash": stable_hash(target_source),
                "content_sha256": hashlib.sha256(
                    target_source.encode("utf-8")
                ).hexdigest(),
            },
            "support": [
                {"path": row.path, "content_sha256": row.content_sha256}
                for row in rows
            ],
            "support_build_order": list(support_build_order),
        }
    )


def model_authored_lean_project(
    *,
    target_source: str,
    project_files: Any = (),
    support_build_order: Sequence[str] = (),
) -> dict[str, Any]:
    rows = normalized_lean_project_files(project_files)
    project_hash = lean_project_hash(
        target_source=target_source,
        project_files=rows,
        support_build_order=support_build_order,
    )
    return {
        "schema_version": 1,
        "artifact_kind": LEAN_PROJECT_ARTIFACT_KIND,
        "main_path": LEAN_PROJECT_MAIN_PATH,
        "main_source_hash": stable_hash(target_source),
        "support_files": [row.to_json() for row in rows],
        "support_build_order": list(support_build_order),
        "project_hash": project_hash,
        "runtime_edited_source": False,
    }


def load_model_authored_lean_project(
    value: Any,
    *,
    target_source: str,
) -> tuple[tuple[LeanProjectFile, ...], tuple[str, ...]]:
    if value in (None, {}):
        return (), ()
    if not isinstance(value, Mapping):
        raise ValueError("model-authored Lean project must be an object")
    if value.get("artifact_kind") == LEAN_PROJECT_REFERENCE_KIND:
        value = _load_model_authored_lean_project_reference(value)
    if value.get("artifact_kind") != LEAN_PROJECT_ARTIFACT_KIND:
        raise ValueError("model-authored Lean project kind mismatch")
    if value.get("schema_version") != 1:
        raise ValueError("model-authored Lean project schema mismatch")
    if value.get("main_path") != LEAN_PROJECT_MAIN_PATH:
        raise ValueError("model-authored Lean project main path mismatch")
    if value.get("runtime_edited_source") is not False:
        raise ValueError("model-authored Lean project crossed runtime source ownership")
    if str(value.get("main_source_hash", "") or "") != stable_hash(target_source):
        raise ValueError("model-authored Lean project target source hash mismatch")
    rows = normalized_lean_project_files(value.get("support_files", []))
    build_order = tuple(value.get("support_build_order", []) or [])
    errors = lean_project_build_order_errors(
        build_order,
        project_files=rows,
        require_complete=True,
    )
    if errors:
        raise ValueError("; ".join(errors))
    expected_hash = lean_project_hash(
        target_source=target_source,
        project_files=rows,
        support_build_order=build_order,
    )
    if str(value.get("project_hash", "") or "") != expected_hash:
        raise ValueError("model-authored Lean project hash mismatch")
    return rows, build_order


def _load_model_authored_lean_project_reference(
    reference: Mapping[str, Any],
) -> Mapping[str, Any]:
    root = Path(str(reference.get("root_path", "") or "")).expanduser().resolve()
    relative = PurePosixPath(str(reference.get("relative_path", "") or ""))
    if (
        reference.get("schema_version") != 1
        or reference.get("runtime_edited_source") is not False
        or relative.is_absolute()
        or not relative.parts
        or relative.parts[0] != LEAN_PROJECT_REFERENCE_DIRECTORY
        or ".." in relative.parts
    ):
        raise ValueError("model-authored Lean project reference identity mismatch")
    path = (root / Path(relative)).resolve()
    if root != path and root not in path.parents:
        raise ValueError("model-authored Lean project reference escapes its workspace")
    try:
        encoded = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"model-authored Lean project reference unreadable: {exc}") from exc
    if hashlib.sha256(encoded).hexdigest() != str(
        reference.get("sha256", "") or ""
    ):
        raise ValueError("model-authored Lean project reference hash mismatch")
    try:
        payload = json.loads(encoded.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("model-authored Lean project reference is not valid JSON") from exc
    if not isinstance(payload, Mapping) or any(
        str(reference.get(field, "") or "")
        != str(payload.get(field, "") or "")
        for field in ("main_source_hash", "project_hash")
    ):
        raise ValueError("model-authored Lean project reference payload mismatch")
    reference_file_count = reference.get("support_file_count")
    if (
        isinstance(reference_file_count, bool)
        or not isinstance(reference_file_count, int)
        or reference_file_count != len(payload.get("support_files", []) or [])
    ):
        raise ValueError("model-authored Lean project reference file count mismatch")
    return payload


def canonical_model_authored_lean_project(
    value: Any,
    *,
    target_source: str,
) -> dict[str, Any]:
    """Validate and canonicalize the exact project owned by the model."""

    rows, build_order = load_model_authored_lean_project(
        value,
        target_source=target_source,
    )
    return model_authored_lean_project(
        target_source=target_source,
        project_files=rows,
        support_build_order=build_order,
    )


def validated_model_authored_lean_project_artifact(
    value: Any,
    *,
    target_source: str,
) -> dict[str, Any]:
    """Preserve a valid content reference, or canonicalize an inline project."""

    canonical = canonical_model_authored_lean_project(
        value,
        target_source=target_source,
    )
    if isinstance(value, Mapping) and value.get("artifact_kind") == (
        LEAN_PROJECT_REFERENCE_KIND
    ):
        return dict(value)
    return canonical


def persist_model_authored_lean_project(
    value: Any,
    *,
    target_source: str,
    root: Path | None,
) -> dict[str, Any]:
    """Persist one immutable project body and return its compact reference."""

    canonical = canonical_model_authored_lean_project(
        value,
        target_source=target_source,
    )
    if root is None:
        return canonical
    workspace_root = Path(root).expanduser().resolve()
    encoded = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    sha256 = hashlib.sha256(encoded).hexdigest()
    relative = PurePosixPath(
        LEAN_PROJECT_REFERENCE_DIRECTORY,
        f"{sha256}.json",
    )
    path = (workspace_root / Path(relative)).resolve()
    if workspace_root != path and workspace_root not in path.parents:
        raise ValueError("model-authored Lean project path escapes its workspace")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != encoded:
        raise ValueError("model-authored Lean project path contains different bytes")
    if not path.exists():
        path.write_bytes(encoded)
    return {
        "schema_version": 1,
        "artifact_kind": LEAN_PROJECT_REFERENCE_KIND,
        "root_path": str(workspace_root),
        "relative_path": relative.as_posix(),
        "sha256": sha256,
        "main_source_hash": canonical["main_source_hash"],
        "project_hash": canonical["project_hash"],
        "support_file_count": len(canonical["support_files"]),
        "runtime_edited_source": False,
    }


def materialize_lean_project_workspace(
    *,
    workspace_root: Path,
    target_source: str | None,
    project_files: Any,
) -> tuple[Path, tuple[LeanProjectFile, ...]]:
    """Write only the exact declared project files into a clean workspace."""

    root = Path(workspace_root).expanduser().resolve()
    rows = normalized_lean_project_files(project_files)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = root / PurePosixPath(row.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(row.content, encoding="utf-8")
    target_path = root / LEAN_PROJECT_MAIN_PATH
    if target_source is not None:
        target_path.write_text(target_source, encoding="utf-8")
    return target_path, rows


def lean_project_tool_environment(
    *,
    active_project: Path,
    search_roots: Sequence[Path],
    timeout_s: int,
) -> tuple[str, dict[str, str]]:
    """Resolve one active Lake toolchain with explicit additional module roots."""

    project = Path(active_project).expanduser().resolve()
    try:
        lean = subprocess.run(
            ["lake", "env", "which", "lean"],
            cwd=str(project),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        lean_path = subprocess.run(
            ["lake", "env", "printenv", "LEAN_PATH"],
            cwd=str(project),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Lean project environment unavailable: {exc}") from exc
    if lean.returncode != 0 or lean_path.returncode != 0:
        detail = "\n".join(
            value.strip()
            for value in (lean.stdout, lean.stderr, lean_path.stdout, lean_path.stderr)
            if value.strip()
        )
        raise RuntimeError("Lean project environment probe failed: " + detail)
    lean_binary = lean.stdout.strip()
    if not lean_binary:
        raise RuntimeError("Lean project environment omitted the Lean executable")
    roots = tuple(
        dict.fromkeys(str(Path(root).expanduser().resolve()) for root in search_roots)
    )
    base_path = lean_path.stdout.strip()
    environment = dict(os.environ)
    environment["LEAN_PATH"] = os.pathsep.join(
        [*roots, *([base_path] if base_path else [])]
    )
    return lean_binary, environment


class LeanProjectExecutor:
    """Compile exact model-authored Lean project files in one pinned Lake environment."""

    def __init__(
        self,
        *,
        active_project: Path,
        workspace_root: Path,
        timeout_s: int,
    ) -> None:
        self.active_project = Path(active_project).expanduser().resolve()
        self.workspace_root = Path(workspace_root).expanduser().resolve()
        self.timeout_s = max(1, int(timeout_s))
        self._tool_cache: tuple[str, dict[str, str]] | None = None
        self._support_state_hash = ""
        self._successful_build_order: tuple[str, ...] = ()

    def _tool_environment(self) -> tuple[str, dict[str, str]]:
        if self._tool_cache is not None:
            lean_binary, environment = self._tool_cache
            return lean_binary, dict(environment)
        lean_binary, environment = lean_project_tool_environment(
            active_project=self.active_project,
            search_roots=(self.workspace_root,),
            timeout_s=self.timeout_s,
        )
        self._tool_cache = (lean_binary, dict(environment))
        return lean_binary, environment

    def _materialize(
        self,
        *,
        target_source: str | None,
        project_files: Sequence[LeanProjectFile],
    ) -> Path:
        target_path, rows = materialize_lean_project_workspace(
            workspace_root=self.workspace_root,
            target_source=target_source,
            project_files=project_files,
        )
        self._support_state_hash = stable_hash(
            [(row.path, row.content_sha256) for row in rows]
        )
        self._successful_build_order = ()
        return target_path

    def _support_prefix_reusable(
        self,
        *,
        project_files: Sequence[LeanProjectFile],
        support_build_order: Sequence[str],
    ) -> bool:
        state_hash = stable_hash(
            [(row.path, row.content_sha256) for row in project_files]
        )
        if not (
            self.workspace_root.is_dir()
            and self._support_state_hash == state_hash
            and self._successful_build_order == tuple(support_build_order)
        ):
            return False
        rows_by_path = {row.path: row for row in project_files}
        for row in project_files:
            source_path = self.workspace_root / PurePosixPath(row.path)
            try:
                source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
            except OSError:
                return False
            if source_sha256 != row.content_sha256:
                return False
        for relative_path in support_build_order:
            row = rows_by_path.get(relative_path)
            if row is None or not (
                self.workspace_root / PurePosixPath(relative_path)
            ).with_suffix(".olean").is_file():
                return False
        return True

    def _write_target_preserving_support(self, target_source: str) -> Path:
        target_path = self.workspace_root / LEAN_PROJECT_MAIN_PATH
        for suffix in (
            ".olean",
            ".ilean",
            ".candidate_identity_probe.lean",
            ".candidate_identity_probe.olean",
            ".candidate_identity_probe.ilean",
        ):
            generated = target_path.with_suffix(suffix)
            try:
                generated.unlink()
            except FileNotFoundError:
                pass
        target_path.write_text(target_source, encoding="utf-8")
        return target_path

    def _compile_support(
        self,
        *,
        lean_binary: str,
        environment: Mapping[str, str],
        relative_path: str,
    ) -> dict[str, Any]:
        source_path = self.workspace_root / PurePosixPath(relative_path)
        output_path = source_path.with_suffix(".olean")
        # Support compilation admits sketches; the target's transitive axiom audit
        # remains the authority for closure, including imported sorryAx.
        command = [
            lean_binary,
            "-R",
            str(self.workspace_root),
            "-o",
            str(output_path),
            str(source_path),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=str(self.active_project),
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                env=dict(environment),
            )
            return {
                "relative_path": relative_path,
                "compiled": completed.returncode == 0,
                "exit_status": str(int(completed.returncode)),
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "command": command,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "relative_path": relative_path,
                "compiled": False,
                "exit_status": "timeout",
                "stdout": str(exc.stdout or "").strip(),
                "stderr": f"timeout after {self.timeout_s}s: {exc.stderr or ''}".strip(),
                "command": command,
            }
        except OSError as exc:
            return {
                "relative_path": relative_path,
                "compiled": False,
                "exit_status": "execution_error",
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
                "command": command,
            }

    def check_support_file(
        self,
        *,
        relative_path: str,
        project_files: Any,
        prior_build_order: Sequence[str],
    ) -> dict[str, Any]:
        rows = normalized_lean_project_files(project_files)
        source_path = self.workspace_root / PurePosixPath(relative_path)
        errors = lean_project_build_order_errors(
            prior_build_order,
            project_files=rows,
            require_complete=False,
        )
        known = {row.path for row in rows}
        if relative_path not in known:
            errors.append(f"unknown Lean support file: {relative_path}")
        if relative_path in prior_build_order:
            errors.append(
                "Lean support file is already in the current successful build order"
            )
        if errors:
            raise ValueError("; ".join(errors))
        reuse_prefix = self._support_prefix_reusable(
            project_files=rows,
            support_build_order=prior_build_order,
        )
        if not reuse_prefix:
            self._materialize(target_source=None, project_files=rows)
        try:
            lean_binary, environment = self._tool_environment()
        except RuntimeError as exc:
            return {
                "relative_path": relative_path,
                "source_hash": stable_hash(
                    next(row.content for row in rows if row.path == relative_path)
                ),
                "compiled": False,
                "artifact_path": str(source_path),
                "proof_state_artifact_path": str(source_path),
                "compiled_prefix_reused": False,
                "compiled_prefix_rebuilt": False,
                "support_build_attempts": [],
                "local_lean_exit_status": "environment_error",
                "local_lean_stdout": "",
                "local_lean_stderr": str(exc),
                "local_lean_command": [],
                "runtime_edited_source": False,
                "proof_evidence_status": (
                    "LEAN_SUPPORT_FILE_CHECK_NOT_TARGET_PROOF_EVIDENCE"
                ),
            }
        attempts = []
        for path in [*([] if reuse_prefix else prior_build_order), relative_path]:
            attempt = self._compile_support(
                lean_binary=lean_binary,
                environment=environment,
                relative_path=path,
            )
            attempts.append(attempt)
            if not attempt["compiled"]:
                break
        latest = attempts[-1]
        prefix_rebuilt = not reuse_prefix and bool(prior_build_order)
        compiled = bool(
            len(attempts)
            == (1 if reuse_prefix else len(prior_build_order) + 1)
            and latest["compiled"]
        )
        if compiled:
            self._successful_build_order = (
                *tuple(prior_build_order),
                relative_path,
            )
        return {
            "relative_path": relative_path,
            "source_hash": stable_hash(
                next(row.content for row in rows if row.path == relative_path)
            ),
            "compiled": compiled,
            "artifact_path": str(source_path),
            "proof_state_artifact_path": str(source_path),
            "compiled_prefix_reused": reuse_prefix,
            "compiled_prefix_rebuilt": prefix_rebuilt,
            "support_build_attempts": attempts,
            "local_lean_exit_status": latest["exit_status"],
            "local_lean_stdout": latest["stdout"],
            "local_lean_stderr": latest["stderr"],
            "local_lean_command": latest["command"],
            "runtime_edited_source": False,
            "proof_evidence_status": "LEAN_SUPPORT_FILE_CHECK_NOT_TARGET_PROOF_EVIDENCE",
        }

    def check_target(
        self,
        *,
        target_source: str,
        candidate_lean_declaration: str,
        project_files: Any,
        support_build_order: Sequence[str],
    ) -> dict[str, Any]:
        rows = normalized_lean_project_files(project_files)
        errors = lean_project_build_order_errors(
            support_build_order,
            project_files=rows,
            require_complete=True,
        )
        if errors:
            raise ValueError("; ".join(errors))
        reuse_support_prefix = self._support_prefix_reusable(
            project_files=rows,
            support_build_order=support_build_order,
        )
        target_path = (
            self._write_target_preserving_support(target_source)
            if reuse_support_prefix
            else self._materialize(
                target_source=target_source,
                project_files=rows,
            )
        )
        project = model_authored_lean_project(
            target_source=target_source,
            project_files=rows,
            support_build_order=support_build_order,
        )
        try:
            lean_binary, environment = self._tool_environment()
        except RuntimeError as exc:
            return {
                "source_hash": stable_hash(target_source),
                "candidate_lean_declaration": candidate_lean_declaration,
                "compiled": False,
                "artifact_path": str(target_path),
                "proof_state_artifact_path": str(target_path),
                "proof_state_search_root": str(self.workspace_root),
                "local_lean_attempted": True,
                "local_lean_compiled": False,
                "local_lean_source_compiled": False,
                "local_lean_source_exit_status": "environment_error",
                "local_lean_exit_status": "environment_error",
                "local_lean_stdout": "",
                "local_lean_stderr": str(exc),
                "local_lean_command": [],
                "candidate_identity_lean_checked": False,
                "candidate_identity_lean_verified": False,
                "candidate_axiom_audit_checked": False,
                "candidate_axiom_audit_clean": False,
                "support_build_attempts": [],
                "compiled_support_prefix_reused": reuse_support_prefix,
                "lean_project": project,
                "lean_project_hash": project["project_hash"],
            }
        support_attempts = []
        for relative_path in (() if reuse_support_prefix else support_build_order):
            attempt = self._compile_support(
                lean_binary=lean_binary,
                environment=environment,
                relative_path=relative_path,
            )
            support_attempts.append(attempt)
            if not attempt["compiled"]:
                return {
                    "source_hash": stable_hash(target_source),
                    "candidate_lean_declaration": candidate_lean_declaration,
                    "compiled": False,
                    "artifact_path": str(target_path),
                    "proof_state_artifact_path": str(target_path),
                    "proof_state_search_root": str(self.workspace_root),
                    "local_lean_attempted": True,
                    "local_lean_compiled": False,
                    "local_lean_source_compiled": False,
                    "local_lean_source_exit_status": "support_build_failed",
                    "local_lean_exit_status": "support_build_failed",
                    "local_lean_stdout": attempt["stdout"],
                    "local_lean_stderr": attempt["stderr"],
                    "local_lean_command": attempt["command"],
                    "candidate_identity_lean_checked": False,
                    "candidate_identity_lean_verified": False,
                    "candidate_axiom_audit_checked": False,
                    "candidate_axiom_audit_clean": False,
                    "support_build_attempts": support_attempts,
                    "compiled_support_prefix_reused": reuse_support_prefix,
                    "lean_project": model_authored_lean_project(
                        target_source=target_source,
                        project_files=rows,
                        support_build_order=support_build_order,
                    ),
                }
        self._successful_build_order = tuple(support_build_order)
        local_result = dict(
            run_lean_candidate_identity_probe(
                artifact_path=target_path,
                candidate_lean_declaration=candidate_lean_declaration,
                lean_project=self.active_project,
                lean_timeout=self.timeout_s,
                lean_command=(
                    lean_binary,
                    "-R",
                    str(self.workspace_root),
                ),
                lean_environment=environment,
            )
        )
        return {
            "source_hash": stable_hash(target_source),
            "candidate_lean_declaration": candidate_lean_declaration,
            "compiled": bool(local_result.get("local_lean_compiled", False)),
            "artifact_path": str(target_path),
            "proof_state_artifact_path": str(target_path),
            "proof_state_search_root": str(self.workspace_root),
            **local_result,
            "support_build_attempts": support_attempts,
            "compiled_support_prefix_reused": reuse_support_prefix,
            "lean_project": project,
            "lean_project_hash": project["project_hash"],
        }

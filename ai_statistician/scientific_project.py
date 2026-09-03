from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


MAX_SCIENTIFIC_PROJECT_FILES = 64
MAX_SCIENTIFIC_PROJECT_BYTES = 2 * 1024 * 1024
MAX_SCIENTIFIC_PROJECT_FILE_BYTES = 512 * 1024


@dataclass(frozen=True)
class ScientificProjectFile:
    path: str
    content: str
    content_sha256: str

    def to_json(self) -> dict[str, str]:
        return {
            "path": self.path,
            "content": self.content,
            "content_sha256": self.content_sha256,
        }


def scientific_main_path(language: str) -> str:
    return "main.R" if str(language).strip().lower() == "r" else "main.py"


def _project_path_error(path: str, *, language: str) -> str:
    pure = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or "\x00" in path
        or pure.is_absolute()
        or path != pure.as_posix()
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        return f"scientific project path is not canonical and relative: {path!r}"
    if path == scientific_main_path(language):
        return f"scientific project support file collides with {path}"
    return ""


def scientific_project_file_errors(
    value: Any,
    *,
    language: str,
) -> list[str]:
    if value in (None, ()):
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ["scientific project_files must be an array"]
    if len(value) > MAX_SCIENTIFIC_PROJECT_FILES:
        return [
            f"scientific project exceeds {MAX_SCIENTIFIC_PROJECT_FILES} support files"
        ]
    errors: list[str] = []
    paths: set[str] = set()
    total_bytes = 0
    for index, raw in enumerate(value):
        if isinstance(raw, ScientificProjectFile):
            path, content = raw.path, raw.content
            supplied_sha256 = raw.content_sha256
        elif isinstance(raw, Mapping):
            unexpected = set(raw) - {"path", "content", "content_sha256"}
            if unexpected:
                errors.append(
                    f"scientific project file {index} has unexpected fields: "
                    + ", ".join(sorted(unexpected))
                )
            path, content = raw.get("path"), raw.get("content")
            supplied_sha256 = raw.get("content_sha256", "")
        else:
            errors.append(f"scientific project file {index} must be an object")
            continue
        if not isinstance(path, str) or not isinstance(content, str):
            errors.append(
                f"scientific project file {index} requires text path and content"
            )
            continue
        path_error = _project_path_error(path, language=language)
        if path_error:
            errors.append(path_error)
        if path in paths:
            errors.append(f"duplicate scientific project path: {path}")
        paths.add(path)
        encoded = content.encode("utf-8")
        total_bytes += len(encoded)
        if len(encoded) > MAX_SCIENTIFIC_PROJECT_FILE_BYTES:
            errors.append(f"scientific project file exceeds size boundary: {path}")
        observed_sha256 = hashlib.sha256(encoded).hexdigest()
        if supplied_sha256 and supplied_sha256 != observed_sha256:
            errors.append(f"scientific project file hash mismatch: {path}")
    if total_bytes > MAX_SCIENTIFIC_PROJECT_BYTES:
        errors.append("scientific project support files exceed aggregate size boundary")
    return sorted(set(errors))


def normalized_scientific_project_files(
    value: Any,
    *,
    language: str,
) -> tuple[ScientificProjectFile, ...]:
    rows = [] if value in (None, ()) else value
    errors = scientific_project_file_errors(rows, language=language)
    if errors:
        raise ValueError("; ".join(errors))
    normalized = []
    for raw in rows:
        path = raw.path if isinstance(raw, ScientificProjectFile) else str(raw["path"])
        content = raw.content if isinstance(raw, ScientificProjectFile) else str(raw["content"])
        normalized.append(
            ScientificProjectFile(
                path=path,
                content=content,
                content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(sorted(normalized, key=lambda row: row.path))


def scientific_project_file_rows(
    value: Any,
    *,
    language: str,
) -> list[dict[str, str]]:
    return [
        row.to_json()
        for row in normalized_scientific_project_files(value, language=language)
    ]


def scientific_project_hash(
    *,
    language: str,
    code: str,
    project_files: Any = (),
) -> str:
    rows = normalized_scientific_project_files(project_files, language=language)
    return stable_hash(
        {
            "language": language,
            "main": {
                "path": scientific_main_path(language),
                "content_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
            },
            "support": [
                {"path": row.path, "content_sha256": row.content_sha256}
                for row in rows
            ],
        }
    )


def scientific_project_files_json_schema() -> dict[str, Any]:
    return {
        "type": "array",
        "maxItems": MAX_SCIENTIFIC_PROJECT_FILES,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["path", "content"],
            "properties": {
                "path": {"type": "string", "minLength": 1},
                "content": {
                    "type": "string",
                    "maxLength": MAX_SCIENTIFIC_PROJECT_FILE_BYTES,
                },
            },
        },
    }


def scientific_python_local_import_roots(
    project_files: Sequence[ScientificProjectFile],
) -> set[str]:
    roots = set()
    for row in project_files:
        if PurePosixPath(row.path).suffix != ".py":
            continue
        first = PurePosixPath(row.path).parts[0]
        roots.add(first[:-3] if first.endswith(".py") else first)
    return roots

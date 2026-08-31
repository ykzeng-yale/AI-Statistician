from __future__ import annotations

import hashlib

import pytest

from ai_statistician.scientific_project import (
    normalized_scientific_project_files,
    scientific_project_file_errors,
    scientific_project_hash,
)


def test_scientific_project_hash_binds_every_file_independent_of_input_order() -> None:
    code = "from package.value import VALUE\n"
    files = [
        {"path": "package/value.py", "content": "VALUE = 3\n"},
        {"path": "package/__init__.py", "content": "# package\n"},
    ]

    first = scientific_project_hash(
        language="python", code=code, project_files=files
    )
    second = scientific_project_hash(
        language="python", code=code, project_files=list(reversed(files))
    )
    changed = scientific_project_hash(
        language="python",
        code=code,
        project_files=[
            files[0],
            {"path": "package/__init__.py", "content": "# changed\n"},
        ],
    )

    assert first == second
    assert changed != first


@pytest.mark.parametrize(
    ("language", "project_files", "message"),
    [
        ("python", [{"path": "../helper.py", "content": "X = 1\n"}], "canonical"),
        ("python", [{"path": "helper.R", "content": "x <- 1\n"}], "must end in .py"),
        ("r", [{"path": "main.R", "content": "x <- 1\n"}], "collides"),
        (
            "python",
            [
                {"path": "helper.py", "content": "X = 1\n"},
                {"path": "helper.py", "content": "X = 2\n"},
            ],
            "duplicate",
        ),
    ],
)
def test_scientific_project_rejects_unsafe_or_ambiguous_file_sets(
    language: str,
    project_files: list[dict[str, str]],
    message: str,
) -> None:
    errors = scientific_project_file_errors(project_files, language=language)
    assert any(message in error for error in errors)
    with pytest.raises(ValueError, match=message):
        normalized_scientific_project_files(project_files, language=language)


def test_scientific_project_rejects_stale_supplied_content_hash() -> None:
    content = "VALUE = 3\n"
    errors = scientific_project_file_errors(
        [
            {
                "path": "helper.py",
                "content": content,
                "content_sha256": hashlib.sha256(b"different").hexdigest(),
            }
        ],
        language="python",
    )
    assert errors == ["scientific project file hash mismatch: helper.py"]

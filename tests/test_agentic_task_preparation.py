from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.prepare_agentic_task import SKILL, main, prepare_task


@pytest.fixture(autouse=True)
def prohibit_network_and_process_launch(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("task preparation must only read and write local files")

    monkeypatch.setattr("socket.socket", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)
    monkeypatch.setattr("subprocess.Popen", forbidden)
    monkeypatch.setattr("os.system", forbidden)


def file_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def sections(task):
    # Heading contract inspected at upstream 2b8aa392; never import/execute upstream.
    matches = list(re.finditer(r"^#{1,6}\s+(.+?)\s*$", task, re.MULTILINE))
    assert [match.group(1) for match in matches] == ["Goal", "Rubrics", "Constraints"]
    return {match.group(1): task[match.end():matches[index + 1].start()
                               if index + 1 < len(matches) else len(task)].strip()
            for index, match in enumerate(matches)}


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_cli_preserves_full_brief_and_quotes_headings(tmp_path, monkeypatch, newline):
    text = newline.join([
        "# Opaque brief", "", "## Context", "opaque \u03bb \u4e2d {marker}",
        "# Goal", "opaque goal", "### Rubrics", "opaque criteria", "> nested quote",
        "```md", "# Constraints", "opaque fenced text", "```", "###### Tail", "",
    ])
    original = text.encode("utf-8")
    brief = tmp_path / "opaque.md"
    brief.write_bytes(original)
    before = brief.stat()
    monkeypatch.chdir(tmp_path)
    assert main(["--brief", "opaque.md", "--destination", "nested/task"]) == 0
    destination = tmp_path / "nested" / "task"
    assert (destination / "resources/search/research_brief.md").read_bytes() == original
    assert brief.read_bytes() == original
    assert brief.stat().st_mtime_ns == before.st_mtime_ns
    task = (destination / "task.md").read_text(encoding="utf-8")
    parsed = sections(task)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    quoted = "> " + normalized.replace("\n", "\n> ")
    assert quoted.strip() in parsed["Goal"]
    assert "opaque fenced text" in parsed["Goal"]
    assert "opaque criteria" not in parsed["Rubrics"]
    assert all(parsed.values())
    for forbidden in (str(tmp_path), str(SKILL), "/Users/", "AgentRuntime", "API_KEY"):
        assert forbidden not in task


def test_copies_only_existing_markdown_guidance_and_is_deterministic(tmp_path):
    brief = tmp_path / "opaque.md"
    brief.write_bytes(b"Opaque preparation fixture, not a scientific result.\n")
    first, second = tmp_path / "first", tmp_path / "second"
    assert prepare_task(brief, first) == first
    prepare_task(brief, second)
    expected = {"SKILL.md": (SKILL / "SKILL.md").read_bytes()}
    expected.update({path.relative_to(SKILL).as_posix(): path.read_bytes()
                     for path in (SKILL / "references").rglob("*.md")})
    assert file_bytes(first / "resources/search/statistical-research") == expected
    assert set(file_bytes(first)) == {
        "task.md", "resources/search/research_brief.md",
        *("resources/search/statistical-research/" + name for name in expected),
    }
    assert file_bytes(first) == file_bytes(second)
    for path in first.rglob("*"):
        assert not path.is_symlink()
    task = (first / "task.md").read_text(encoding="utf-8")
    for link in re.findall(r"\]\((resources/[^)]+)\)", task):
        assert (first / link).is_file()
    before = file_bytes(first)
    with pytest.raises(FileExistsError):
        prepare_task(brief, first)
    assert file_bytes(first) == before


def test_goal_and_rubrics_keep_scientific_evidence_boundaries(tmp_path):
    brief = tmp_path / "opaque.md"
    brief.write_bytes(b"Opaque intent.\n")
    destination = prepare_task(brief, tmp_path / "task")
    parsed = sections((destination / "task.md").read_text(encoding="utf-8"))
    for clause in (
        "resources/search/statistical-research/SKILL.md", "known-method", "permitted-source",
        "Source-assisted", "hidden judge", "Markdown/LaTeX", "Python/R",
        "exploratory", "Freeze confirmatory", "precision/stopping", "failures",
        "Lean is optional unless task intent explicitly requires formal proof",
        "exact target identity", "axiom-clean", "independent review", "unreviewed",
        "report", "honest gaps",
    ):
        assert clause in parsed["Goal"]
    assert "Native evaluator/JSON scoring and self-rubrics are not mathematical proof" in parsed["Rubrics"]
    assert "consumed evaluations" in parsed["Constraints"]


@pytest.mark.parametrize("kind", ["empty_dir", "prior_task", "file", "dir_link", "file_link", "dangling_link"])
def test_refuses_every_existing_destination_without_changes(tmp_path, kind):
    brief = tmp_path / "opaque.md"
    original = b"Opaque input, unchanged.\n"
    brief.write_bytes(original)
    prior = tmp_path / "prior"
    prior.mkdir()
    (prior / "task.md").write_bytes(b"Opaque prior task, unchanged.\n")
    destination = tmp_path / "destination"
    if kind == "empty_dir":
        destination.mkdir()
    elif kind == "prior_task":
        destination = prior
    elif kind == "file":
        destination.write_bytes(b"Opaque existing file.\n")
    else:
        target = {"dir_link": prior, "file_link": brief,
                  "dangling_link": tmp_path / "absent"}[kind]
        destination.symlink_to(target, target_is_directory=kind == "dir_link")
    before = file_bytes(tmp_path)
    link = destination.readlink() if destination.is_symlink() else None
    with pytest.raises(FileExistsError):
        prepare_task(brief, destination)
    assert file_bytes(tmp_path) == before
    assert brief.read_bytes() == original
    if link is not None:
        assert destination.is_symlink() and destination.readlink() == link
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("content", [None, b"\xff", b"", b" \r\n\t"])
def test_invalid_input_creates_no_task(tmp_path, content):
    brief = tmp_path / "opaque.md"
    if content is not None:
        brief.write_bytes(content)
    destination = tmp_path / "new-parent" / "task"
    with pytest.raises((OSError, UnicodeError, ValueError)):
        prepare_task(brief, destination)
    assert not destination.parent.exists()
    if content is not None:
        assert brief.read_bytes() == content


def test_cli_reports_bad_input_without_materializing_task(tmp_path, capsys):
    destination = tmp_path / "task"
    with pytest.raises(SystemExit) as exc:
        main(["--brief", str(tmp_path / "absent.md"), "--destination", str(destination)])
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err
    assert not destination.exists()


def test_destination_cannot_be_the_brief(tmp_path):
    brief = tmp_path / "opaque.md"
    original = b"Opaque input.\n"
    brief.write_bytes(original)
    with pytest.raises(FileExistsError):
        prepare_task(brief, brief)
    assert brief.read_bytes() == original

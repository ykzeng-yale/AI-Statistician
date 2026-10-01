from __future__ import annotations

import json
import os
import re
import selectors
import shutil
import subprocess
import time
from pathlib import Path

import pytest


SKILL = Path(__file__).resolve().parents[1] / "skills" / "statistical-research"


@pytest.mark.parametrize("discovery", [".agents/skills", ".claude/skills"])
def test_portable_project_link_keeps_relative_references(tmp_path, discovery):
    copied = tmp_path / "skills" / SKILL.name
    shutil.copytree(SKILL, copied)
    destination = tmp_path / discovery / SKILL.name
    destination.parent.mkdir(parents=True)
    destination.symlink_to("../../skills/" + SKILL.name, target_is_directory=True)

    assert destination.resolve() == copied
    assert (destination / "SKILL.md").read_bytes() == (SKILL / "SKILL.md").read_bytes()
    for reference in re.findall(r"\]\((references/[^)]+)\)", (destination / "SKILL.md").read_text()):
        assert (destination / reference).is_file()
        assert (destination / reference).resolve().is_relative_to(copied)
    with pytest.raises(FileExistsError):
        destination.symlink_to(copied, target_is_directory=True)


@pytest.mark.skipif(
    os.environ.get("AI_STATISTICIAN_CODEX_SKILL_CONFORMANCE") != "1",
    reason="opt-in native Codex skill discovery; no model turn",
)
def test_native_codex_discovers_portable_skill_without_a_model_turn(tmp_path):
    executable = shutil.which("codex")
    assert executable is not None
    project = tmp_path / "project"
    destination = project / ".agents" / "skills" / SKILL.name
    destination.parent.mkdir(parents=True)
    destination.symlink_to(SKILL, target_is_directory=True)
    home = tmp_path / "codex-home"
    home.mkdir()
    selector = selectors.DefaultSelector()
    with (tmp_path / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(
            [executable, "app-server", "--stdio", "-c", "analytics.enabled=false"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
            env={**os.environ, "CODEX_HOME": str(home)}, cwd=project,
        )
        selector.register(process.stdout, selectors.EVENT_READ)
        buffer = b""

        def send(method, params, request_id=None):
            row = {"method": method, "params": params}
            if request_id is not None:
                row["id"] = request_id
            process.stdin.write(json.dumps(row).encode() + b"\n")
            process.stdin.flush()

        def receive(request_id):
            nonlocal buffer
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    row = json.loads(line)
                    if row.get("id") == request_id:
                        assert "error" not in row, row.get("error")
                        return row["result"]
                if selector.select(max(0, deadline - time.monotonic())):
                    chunk = os.read(process.stdout.fileno(), 65536)
                    assert chunk, "Codex app-server exited before discovery"
                    buffer += chunk
            pytest.fail("Codex skills/list did not respond within 30 seconds")

        try:
            send("initialize", {"clientInfo": {"name": "skill_conformance", "version": "1"}}, 1)
            receive(1)
            send("initialized", {})
            send("skills/list", {"cwds": [str(project)], "forceReload": True}, 2)
            result = receive(2)
            matches = [skill for row in result["data"] for skill in row["skills"]
                       if skill["name"] == SKILL.name]
            assert len(matches) == 1
            assert matches[0]["enabled"] is True
            assert Path(matches[0]["path"]).resolve() == SKILL / "SKILL.md"
        finally:
            selector.close()
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)

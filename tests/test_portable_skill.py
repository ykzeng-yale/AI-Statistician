from __future__ import annotations

import json
import os
import re
import selectors
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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


@pytest.mark.skipif(
    os.environ.get("AI_STATISTICIAN_KIMI_SKILL_CONFORMANCE") != "1",
    reason="opt-in native Kimi Code discovery/activation; no live inference",
)
@pytest.mark.parametrize("activate_skill", [False, True], ids=["discovery", "activation"])
def test_native_kimi_skill_discovery_and_activation_without_live_inference(tmp_path, activate_skill):
    executable = os.environ.get("AI_STATISTICIAN_KIMI_EXECUTABLE") or shutil.which("kimi")
    assert executable is not None
    project = tmp_path / "project"
    destination = project / ".agents" / "skills" / SKILL.name
    destination.parent.mkdir(parents=True)
    destination.symlink_to(SKILL, target_is_directory=True)
    (project / ".git").mkdir()
    home = tmp_path / "home"
    home.mkdir()
    data = home / "kimi-code"
    data.mkdir()
    requests = []

    class NoLiveInference(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append({"path": self.path, "body": body})
            if not activate_skill:
                self.send_error(500, "skill discovery must not call a model")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream" if body.get("stream")
                             else "application/json")
            self.end_headers()
            response = {"id": "transport-conformance", "created": 0,
                        "model": "Qwen3-4B-Instruct-2507"}
            if body.get("stream"):
                response["object"] = "chat.completion.chunk"
                for delta, finish in (({"role": "assistant", "content": "conformance"}, None),
                                      ({}, "stop")):
                    response["choices"] = [{"index": 0, "delta": delta, "finish_reason": finish}]
                    self.wfile.write(("data: " + json.dumps(response) + "\n\n").encode())
                self.wfile.write(b"data: [DONE]\n\n")
            else:
                response["object"] = "chat.completion"
                response["choices"] = [{"index": 0, "finish_reason": "stop",
                                        "message": {"role": "assistant", "content": "conformance"}}]
                self.wfile.write(json.dumps(response).encode())
            self.wfile.flush()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), NoLiveInference)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    (data / "config.toml").write_text(
        'default_model = "local-qwen"\ntelemetry = false\n'
        'builtin_product_skills = false\n'
        '[providers.local]\ntype = "openai"\n'
        f'base_url = "http://127.0.0.1:{server.server_port}/v1"\n'
        'api_key = "local-conformance-placeholder"\n'
        '[models.local-qwen]\nprovider = "local"\n'
        'model = "Qwen3-4B-Instruct-2507"\nmax_context_size = 32768\n',
        encoding="utf-8",
    )
    selector = selectors.DefaultSelector()
    try:
        with (tmp_path / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(
                [executable, "acp"], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=stderr, cwd=project,
                env={"PATH": os.environ["PATH"], "HOME": str(home),
                     "KIMI_CODE_HOME": str(data), "TERM": "dumb"},
            )
            selector.register(process.stdout, selectors.EVENT_READ)
            buffer = b""

            def send(method, params, request_id):
                row = {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}
                process.stdin.write(json.dumps(row).encode() + b"\n")
                process.stdin.flush()

            def receive(predicate):
                nonlocal buffer
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        row = json.loads(line)
                        assert "error" not in row, row.get("error")
                        if predicate(row):
                            return row
                    if selector.select(max(0, deadline - time.monotonic())):
                        chunk = os.read(process.stdout.fileno(), 65536)
                        assert chunk, "Kimi Code exited before skill discovery"
                        buffer += chunk
                pytest.fail("Kimi Code ACP did not respond within 30 seconds")

            try:
                send("initialize", {"protocolVersion": 1, "clientCapabilities": {}}, 1)
                initialized = receive(lambda row: row.get("id") == 1)["result"]
                assert initialized["agentInfo"]["name"] == "Kimi Code CLI"
                send("session/new", {"cwd": str(project), "mcpServers": []}, 2)
                session_id = receive(lambda row: row.get("id") == 2)["result"]["sessionId"]
                update = receive(lambda row: row.get("params", {}).get("update", {}).get(
                    "sessionUpdate") == "available_commands_update")["params"]
                assert update["sessionId"] == session_id
                matches = [command for command in update["update"]["availableCommands"]
                           if command["name"] == "skill:" + SKILL.name]
                assert len(matches) == 1
                assert "statistical methods research" in matches[0]["description"]
                assert requests == []
                if activate_skill:
                    send("session/prompt", {"sessionId": session_id, "prompt": [{
                        "type": "text", "text": "/skill:" + SKILL.name + " transport conformance",
                    }]}, 4)
                    prompted = receive(lambda row: row.get("id") == 4)["result"]
                    assert prompted["stopReason"] == "end_turn"
                    assert len(requests) == 1
                    assert requests[0]["path"] == "/v1/chat/completions"
                    assert requests[0]["body"]["model"] == "Qwen3-4B-Instruct-2507"
                    contents = []
                    for message in requests[0]["body"]["messages"]:
                        content = message.get("content", "")
                        contents.extend([content] if isinstance(content, str) else
                                        [part.get("text", "") for part in content or []])
                    skill_body = (SKILL / "SKILL.md").read_text().split("---", 2)[2].strip()
                    assert any(skill_body in content for content in contents)
                    assert any("transport conformance" in content for content in contents)
                send("session/close", {"sessionId": session_id}, 3)
                receive(lambda row: row.get("id") == 3)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
    finally:
        selector.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

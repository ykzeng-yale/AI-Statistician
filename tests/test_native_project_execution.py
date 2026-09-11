from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

import pytest


@pytest.fixture
def native_project(tmp_path):
    if sys.platform != "darwin" or not shutil.which("sandbox-exec"):
        pytest.skip("native SRT qualification is currently exercised only on macOS")
    if not shutil.which("node") or not (Path(__file__).parents[1] / "node_modules/@anthropic-ai/sandbox-runtime").is_dir():
        pytest.skip("SRT qualification requires the pinned npm development dependency")
    project = tmp_path / "project"
    project.mkdir()
    return project


def run(project, output, command, *, allowed_domains=(), timeout_seconds=30, max_output_bytes=1_000_000):
    """Test-only prototype; no product tool or proof/replication authority."""
    output.mkdir()
    home = output / "home"
    home.mkdir()
    runner = Path(__file__).parent / "fixtures/native_project_runner.mjs"
    invocation = {
        "invocation_id": "srt-qualification:" + uuid.uuid4().hex,
        "command": command, "project_dir": str(project),
        "runtime_read_roots": [sys.base_prefix],
        "allowed_domains": list(allowed_domains), "timeout_seconds": timeout_seconds,
        "max_output_bytes": max_output_bytes, "result_path": str(output / "process.json"),
        "runner_sha256": hashlib.sha256(runner.read_bytes()).hexdigest(),
        "package_lock_sha256": hashlib.sha256((runner.parents[2] / "package-lock.json").read_bytes()).hexdigest(),
    }
    request = (json.dumps(invocation, sort_keys=True) + "\n").encode()
    (output / "request.json").write_bytes(request)
    environment = {
        "HOME": str(home), "CLAUDE_CODE_TMPDIR": str(home),
        "PATH": os.pathsep.join([str(Path(sys.base_prefix) / "bin"), "/usr/bin", "/bin", "/usr/sbin", "/sbin"]),
        "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "TZ": "UTC",
        "PYTHONNOUSERSITE": "1", "R_ENVIRON_USER": os.devnull,
        "R_PROFILE_USER": os.devnull, "R_HISTFILE": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
    }
    stdout_path, stderr_path = output / "stdout.txt", output / "stderr.txt"
    started = time.monotonic()
    # The parent's SRT Unix-domain IPC paths have an OS length limit; child temp
    # files remain in its private home, not this short-lived proxy directory.
    with tempfile.TemporaryDirectory(prefix="ais-srt-", dir="/tmp") as ipc_dir, stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        environment["TMPDIR"] = ipc_dir
        process = subprocess.Popen(
            [shutil.which("node"), str(runner)], cwd=project, env=environment,
            stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, start_new_session=True,
        )
        try:
            process.communicate(request, timeout=timeout_seconds + 30)
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    result = json.loads((output / "process.json").read_text())
    streams = {name: path.read_bytes() for name, path in (("stdout", stdout_path), ("stderr", stderr_path))}
    receipt = {
        **result, "command": command, "request_sha256": hashlib.sha256(request).hexdigest(),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        **{name: raw.decode("utf-8", errors="replace") for name, raw in streams.items()},
        "stream_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in streams.items()},
        "evidence_status": "EXPLORATORY_NATIVE_COMMAND_NOT_REPLICATION_OR_PROOF",
    }
    receipt["ok"] = bool(result["executed"] and result["returncode"] == 0
                         and not result["errors"] and not result["timed_out"] and not result["output_truncated"])
    (output / "receipt.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def test_native_command_isolated_files_environment_and_exact_feedback(native_project, tmp_path, monkeypatch):
    hidden = tmp_path / "host-only.txt"
    hidden.write_text("synthetic-host-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-host-credential")
    code = (
        "import os, pathlib, subprocess, sys\n"
        "pathlib.Path('created.txt').write_text('model-owned file')\n"
        "print('home', os.environ['HOME'])\n"
        "assert 'ANTHROPIC_API_KEY' not in os.environ\n"
        f"secret = pathlib.Path({str(hidden)!r})\n"
        "for target in [secret, pathlib.Path('escape')]:\n"
        "    if target.name == 'escape': target.symlink_to(secret)\n"
        "    try: target.read_text()\n"
        "    except PermissionError: print('read denied')\n"
        "    else: raise AssertionError('host read allowed')\n"
        "try: secret.write_text('changed')\n"
        "except PermissionError: print('write denied')\n"
        "else: raise AssertionError('host write allowed')\n"
        "subprocess.run([sys.executable, '-c', \"print('child ran')\"], check=True)\n"
        "print('opaque stderr', file=sys.stderr)\n"
    )
    command = "python3 -c " + shlex.quote(code)
    receipt = run(native_project, tmp_path / "action", command)
    assert receipt["ok"], receipt
    assert receipt["command"] == command
    assert receipt["stdout"].count("read denied") == 2
    assert "child ran" in receipt["stdout"] and "write denied" in receipt["stdout"]
    assert receipt["stderr"] == "opaque stderr\n"
    assert hidden.read_text() == "synthetic-host-secret"
    assert (native_project / "created.txt").read_text() == "model-owned file"
    assert "synthetic-host" not in receipt["stdout"] + receipt["stderr"]
    assert json.loads((tmp_path / "action/receipt.json").read_text()) == receipt


def test_native_commands_prepare_and_use_a_local_dependency(native_project, tmp_path):
    wheel = native_project / "fixture_dep-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in {
            "fixture_dep.py": "flag = 23\n",
            "fixture_dep-1.0.dist-info/METADATA": "Metadata-Version: 2.1\nName: fixture-dep\nVersion: 1.0\n",
            "fixture_dep-1.0.dist-info/WHEEL": "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            "fixture_dep-1.0.dist-info/RECORD": "",
        }.items():
            archive.writestr(name, content)
    prepare = run(native_project, tmp_path / "prepare", "python3 -m venv --copies .venv")
    assert prepare["ok"], prepare
    install = run(native_project, tmp_path / "install", ".venv/bin/python -m pip install --no-index fixture_dep-1.0-py3-none-any.whl")
    assert install["ok"], install
    execute = run(native_project, tmp_path / "execute", ".venv/bin/python -c 'import fixture_dep; print(fixture_dep.flag)'")
    assert execute["ok"] and execute["stdout"] == "23\n", execute
    assert all(row["evidence_status"] == "EXPLORATORY_NATIVE_COMMAND_NOT_REPLICATION_OR_PROOF"
               for row in (prepare, install, execute))


@pytest.mark.parametrize("command,options,field", [
    ("python3 -c 'import time; time.sleep(10)'", {"timeout_seconds": 1}, "timed_out"),
    ("python3 -c 'print(\"x\" * 10000)'", {"max_output_bytes": 100}, "output_truncated"),
])
def test_native_command_bounds_are_observations(native_project, tmp_path, command, options, field):
    receipt = run(native_project, tmp_path / "bounded", command, **options)
    assert not receipt["ok"] and receipt[field], receipt


def test_native_network_is_proxy_scoped_and_direct_sockets_cannot_bypass(native_project, tmp_path):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"fixture-download")

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    # SRT intentionally excludes loopback from proxying by default. This local
    # proxy fixture must opt in; direct loopback remains denied by the OS below.
    fetch = ("import os, urllib.request, urllib.parse; os.environ['no_proxy'] = ''; os.environ['NO_PROXY'] = ''; "
             "proxy = urllib.parse.urlsplit(os.environ['http_proxy']); "
             "os.environ['http_proxy'] = urllib.parse.urlunsplit(proxy._replace(netloc=proxy.netloc.replace('@localhost:', '@127.0.0.1:'))); "
             f"print(urllib.request.urlopen('http://127.0.0.1:{port}/fixture').read().decode())")
    try:
        denied = run(native_project, tmp_path / "network-denied", "python3 -c " + shlex.quote(fetch))
        assert not denied["ok"] and not requests, denied
        allowed = run(native_project, tmp_path / "network-allowed", "python3 -c " + shlex.quote(fetch), allowed_domains=[f"127.0.0.1:{port}"])
        assert allowed["ok"] and allowed["stdout"] == "fixture-download\n", allowed
        assert requests == ["/fixture"]
        direct = run(native_project, tmp_path / "direct-denied", "python3 -c " + shlex.quote(
            f"import socket; socket.create_connection(('127.0.0.1', {port}), timeout=2)"
        ), allowed_domains=[f"127.0.0.1:{port}"])
        assert not direct["ok"] and requests == ["/fixture"], direct
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.xfail(strict=True, raises=RuntimeError,
                   reason="Not admitted to product: detached macOS child can mutate workspace after receipt")
def test_native_detached_process_lifetime(native_project, tmp_path):
    child_source = ("import pathlib, time\n"
                    "while not pathlib.Path('after-receipt').exists(): time.sleep(0.01)\n"
                    "pathlib.Path('late-write').write_text('still writable')\n"
                    "time.sleep(60)\n")
    code = ("import subprocess, sys; "
            f"p = subprocess.Popen([sys.executable, '-c', {child_source!r}], "
            "start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            "print(p.pid)")
    receipt = run(native_project, tmp_path / "detached", "python3 -c " + shlex.quote(code))
    assert receipt["ok"], receipt
    pid = int(receipt["stdout"].strip())
    try:
        (native_project / "after-receipt").touch()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if (native_project / "late-write").exists():
                raise RuntimeError("Detached child wrote after execution receipt and SRT reset")
            time.sleep(0.01)
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

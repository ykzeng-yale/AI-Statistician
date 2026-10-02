"""Actual process lifecycle with opaque scripts; no model or scientific scoring."""

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from benchmarks.publication import execute_draw


pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX-owned process groups")


def configuration(tmp_path, mode="free_planning"):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"mode": mode}))
    return path


def script_transport(monkeypatch, tmp_path, source):
    script = tmp_path / "opaque_child.py"
    script.write_text(source)
    real_popen, calls = subprocess.Popen, []

    def launch(command, **kwargs):
        calls.append((command, kwargs))
        assert command[1:3] == ["-m", "benchmarks.publication.draw_cli"]
        assert kwargs["start_new_session"] is True
        return real_popen([sys.executable, str(script), *command[3:]], **kwargs)

    monkeypatch.setattr(execute_draw.subprocess, "Popen", launch)
    return calls


def verify_records(out, terminal):
    assert json.loads((out / "terminal.json").read_text()) == terminal
    refs = [terminal["launch_ref"], *terminal["captured_streams"].values()]
    for ref in refs:
        raw = Path(ref["path"]).read_bytes()
        assert ref["sha256"] == hashlib.sha256(raw).hexdigest()
        assert ref["byte_size"] == len(raw)
    assert terminal["elapsed_seconds_including_cleanup"] >= terminal["process_elapsed_seconds"] >= 0
    assert terminal["scientific_evaluation_performed"] is False
    assert terminal["model_server_owned"] is False


@pytest.mark.parametrize("mode", ["free_planning", "same_workflow", "full_collaboration", "no_cross_role_revision"])
@pytest.mark.parametrize("code", [0, 7])
def test_one_launch_preserves_raw_streams_without_inspecting_or_scoring(tmp_path, monkeypatch, mode, code):
    config = configuration(tmp_path, mode)
    calls = script_transport(monkeypatch, tmp_path, f"""
import sys
sys.stdout.buffer.write(b'opaque\\xff observation\\n')
sys.stderr.buffer.write(b'raw\\xfe diagnostic\\n')
raise SystemExit({code})
""")
    out = tmp_path / "record"
    terminal = execute_draw.run_declared_draw(config_path=config, record_dir=out)
    assert terminal["disposition"] == "EXITED" and terminal["returncode"] == code
    assert terminal["config_unchanged_at_termination"] is True
    assert (out / "stdout.log").read_bytes() == b"opaque\xff observation\n"
    assert (out / "stderr.log").read_bytes() == b"raw\xfe diagnostic\n"
    frozen = json.loads((out / "launch.json").read_text())
    assert frozen["command"] == calls[0][0]
    assert frozen["wall_seconds"] is None and frozen["model_server_owned"] is False
    assert not (out / "draw").exists()
    verify_records(out, terminal)
    saved = {path: path.read_bytes() for path in out.iterdir()}
    with pytest.raises(FileExistsError):
        execute_draw.run_declared_draw(config_path=config, record_dir=out)
    assert len(calls) == 1 and all(path.read_bytes() == raw for path, raw in saved.items())


def test_timeout_keeps_partial_source_and_stops_only_its_owned_group(tmp_path, monkeypatch):
    config = configuration(tmp_path)
    descendant_pid = tmp_path / "descendant.pid"
    partial = tmp_path / "partial.md"
    real_popen = subprocess.Popen
    peer = real_popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    calls = script_transport(monkeypatch, tmp_path, f"""
import subprocess, sys, time
from pathlib import Path
Path({str(partial)!r}).write_text('# Unselected incomplete work\\n')
subprocess.Popen([sys.executable, '-c', {("import os, signal, time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(" + repr(str(descendant_pid)) + ").write_text(str(os.getpid())); time.sleep(60)")!r}])
print('before wall expiration', flush=True)
time.sleep(60)
""")
    out = tmp_path / "record"
    try:
        terminal = execute_draw.run_declared_draw(config_path=config, record_dir=out, wall_seconds=1,
                                                   shutdown_grace_seconds=0.1)
        assert terminal["disposition"] == "TIMED_OUT" and terminal["returncode"] < 0
        assert terminal["termination_signals"] == ["SIGTERM", "SIGKILL"]
        assert peer.poll() is None and len(calls) == 1
        assert partial.read_text() == "# Unselected incomplete work\n"
        assert descendant_pid.is_file()
        pid = int(descendant_pid.read_text())
        for _ in range(50):
            with real_popen(["ps", "-o", "stat=", "-p", str(pid)], stdout=subprocess.PIPE, text=True) as observer:
                state = observer.communicate()[0].strip()
            if not state or state.startswith("Z"):
                break
            time.sleep(0.02)
        assert not state or state.startswith("Z")
        assert not (out / "draw" / "final_material.json").exists()
        verify_records(out, terminal)
    finally:
        os.killpg(peer.pid, signal.SIGKILL)
        peer.wait()


def test_real_cli_configuration_failure_is_retained_not_retried(tmp_path):
    config = configuration(tmp_path, "invalid")
    out = tmp_path / "record"
    terminal = execute_draw.run_declared_draw(config_path=config, record_dir=out, wall_seconds=30)
    assert terminal["disposition"] == "EXITED" and terminal["returncode"] != 0
    assert "unsupported study draw mode" in (out / "stderr.log").read_text()
    assert not (out / "draw").exists()
    verify_records(out, terminal)


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan"), True, "1"])
@pytest.mark.parametrize("field", ["wall_seconds", "shutdown_grace_seconds"])
def test_invalid_time_declaration_never_creates_output_or_launches(tmp_path, monkeypatch, field, value):
    calls = []
    monkeypatch.setattr(execute_draw.subprocess, "Popen", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError):
        execute_draw.run_declared_draw(config_path=configuration(tmp_path), record_dir=tmp_path / "record", **{field: value})
    assert calls == [] and not (tmp_path / "record").exists()


def test_launch_failure_still_has_an_immutable_terminal_record(tmp_path, monkeypatch):
    calls = []

    def missing(*args, **kwargs):
        calls.append(args)
        raise FileNotFoundError("opaque launch failure")

    monkeypatch.setattr(execute_draw.subprocess, "Popen", missing)
    out = tmp_path / "record"
    with pytest.raises(FileNotFoundError):
        execute_draw.run_declared_draw(config_path=configuration(tmp_path), record_dir=out)
    terminal = json.loads((out / "terminal.json").read_text())
    assert terminal["disposition"] == "LAUNCH_FAILED" and terminal["pid"] is None
    assert terminal["exception_type"] == "FileNotFoundError" and terminal["returncode"] is None
    assert terminal["termination_signals"] == [] and len(calls) == 1
    verify_records(out, terminal)


def test_interruption_stops_owned_child_and_records_exception_before_propagating(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    created = []

    def launch(command, **kwargs):
        process = real_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
        wait = process.wait
        first = True

        def interrupted(timeout=None):
            nonlocal first
            if first:
                first = False
                raise KeyboardInterrupt()
            return wait(timeout=timeout)

        process.wait = interrupted
        created.append(process)
        return process

    monkeypatch.setattr(execute_draw.subprocess, "Popen", launch)
    out = tmp_path / "record"
    with pytest.raises(KeyboardInterrupt):
        execute_draw.run_declared_draw(config_path=configuration(tmp_path), record_dir=out)
    terminal = json.loads((out / "terminal.json").read_text())
    assert terminal["disposition"] == "INTERRUPTED" and terminal["exception_type"] == "KeyboardInterrupt"
    assert len(created) == 1 and created[0].poll() is not None
    verify_records(out, terminal)


def test_changed_declaration_does_not_become_a_successful_launcher_exit(tmp_path, monkeypatch, capsys):
    config = configuration(tmp_path)
    script_transport(monkeypatch, tmp_path, f"""
from pathlib import Path
Path({str(config)!r}).write_text('{{"mode":"changed after launch"}}')
""")
    out = tmp_path / "record"
    assert execute_draw.main(["--config", str(config), "--out", str(out)]) == 1
    terminal = json.loads(capsys.readouterr().out)
    assert terminal["disposition"] == "EXITED" and terminal["returncode"] == 0
    assert terminal["config_unchanged_at_termination"] is False
    verify_records(out, terminal)

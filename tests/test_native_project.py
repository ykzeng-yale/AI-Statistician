"""Real, explicitly enabled offline native commands; no model or research draws."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ai_statistician import native_project as module
from ai_statistician.client_tool_loop import ClientToolInputError
from ai_statistician.native_project import NativeProject, configured_native_project
PYTHON_IMAGE = "docker.io/library/python@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2"
R_IMAGE = "docker.io/library/r-base@sha256:41d5564375009abf74a63987fd7fb9b44c90b1580b310be10ef973abe92496c3"


@pytest.fixture
def project_factory(tmp_path, monkeypatch):
    executable = os.environ.get("AI_STATISTICIAN_TEST_APPLE_CONTAINER")
    if not executable:
        pytest.skip("explicit Apple container service and preloaded image digests required")
    config = {
        "container_executable": executable, "environments": {"python": PYTHON_IMAGE, "r": R_IMAGE},
        "cpus": 1, "memory_bytes": 536870912, "volume_bytes": 134217728,
        "timeout_seconds": 6, "max_output_bytes": 64000,
    }
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps(config))
    monkeypatch.setenv(module.NATIVE_PROJECT_CONFIG_ENV, str(policy))
    projects = []

    def configured_constructor(**kwargs):
        project = NativeProject(**kwargs)
        projects.append(project)
        return project

    monkeypatch.setattr(module, "NativeProject", configured_constructor)

    def make(**kwargs):
        project = NativeProject(config=config, workspace_dir=tmp_path / "workspace",
                                owner=kwargs.pop("owner", "test"), authorization="synthetic-authority", **kwargs)
        projects.append(project)
        return project

    yield make
    for project in projects:
        if project.state_path.exists():
            state = json.loads(project.state_path.read_text())
            if state.get("pending"):
                project._stop_and_delete(state["pending"]["container"])
            volumes = project._json_control("volume", "list", "--format", "json")
            if any(row["id"] == state["volume"] for row in volumes):
                rows = project._json_control("volume", "inspect", state["volume"])
                assert rows[0]["configuration"]["labels"]["ais.owner"] == project.identity_hash
                project._control("volume", "delete", state["volume"])


def run(project, command, environment="python", **kwargs):
    return project.execute({"environment": environment, "command": command, **kwargs}).content


def test_not_configured_does_not_touch_workspace(tmp_path, monkeypatch):
    monkeypatch.delenv(module.NATIVE_PROJECT_CONFIG_ENV, raising=False)
    assert configured_native_project(tmp_path / "absent", owner="test", authorization="a") is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("config", [None, [], {}, {"environments": []}])
def test_invalid_policy_is_rejected_without_starting_service(tmp_path, config):
    with pytest.raises(ValueError, match="exact environment policy"):
        NativeProject(config=config, workspace_dir=tmp_path, owner="test", authorization="a")


def test_native_exact_feedback_isolation_and_resume(project_factory, tmp_path, monkeypatch):
    project = project_factory()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-secret")
    secret = tmp_path / "private.txt"
    secret.write_text("private")
    result = run(project, "python - <<'PY'\n"
        "import os, pathlib, socket, sys\n"
        "assert os.getuid() != 0\n"
        "assert 'ANTHROPIC_API_KEY' not in os.environ\n"
        "assert 'SSH_AUTH_SOCK' not in os.environ\n"
        f"assert not pathlib.Path({str(secret)!r}).exists()\n"
        f"assert not pathlib.Path({str(project.root)!r}).exists()\n"
        "assert sorted(os.listdir('/sys/class/net')) == ['lo']\n"
        "try: socket.create_connection(('1.1.1.1', 443), timeout=1)\n"
        "except OSError: pass\n"
        "else: raise AssertionError('network reachable')\n"
        "assert int(next(x.split(':')[1].strip() for x in pathlib.Path('/proc/self/status').read_text().splitlines() if x.startswith('CapEff:')), 16) == 0\n"
        "try: pathlib.Path('/etc/writable').write_text('bad')\n"
        "except OSError: pass\n"
        "else: raise AssertionError('writable root')\n"
        "pathlib.Path('counter').write_text('1')\n"
        "print('raw output'); print('raw error', file=sys.stderr); sys.exit(23)\nPY")
    assert result["returncode"] == 23, result
    assert result["stdout"] == "raw output\n"
    assert result["stderr"] == "raw error\n"
    assert result["vm_deleted"]
    resumed = project_factory()
    second = run(resumed, "cat counter")
    assert second["stdout"] == "1", second
    assert second["parent_receipt"]["sha256"] == result["receipt_sha256"]
    assert second["volume_sha256_before"] == result["volume_sha256_after"]
    assert secret.read_text() == "private"
    with pytest.raises(ValueError, match="owner or environment changed"):
        project.identity_hash = "different"
        run(project, "echo forbidden")
    project.identity_hash = resumed.identity_hash


def test_native_local_python_and_r_dependencies_persist(project_factory):
    project = project_factory()
    commands = [
        "python -m venv --copies .venv",
        "python - <<'PY'\nimport zipfile\n"
        "with zipfile.ZipFile('fixture_dep-1.0-py3-none-any.whl', 'w') as z:\n"
        " for path, data in {'fixture_dep.py':'value=31',"
        "'fixture_dep-1.0.dist-info/METADATA':'Metadata-Version: 2.1\\nName: fixture-dep\\nVersion: 1.0\\n',"
        "'fixture_dep-1.0.dist-info/WHEEL':'Wheel-Version: 1.0\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n',"
        "'fixture_dep-1.0.dist-info/RECORD':''}.items(): z.writestr(path, data)\nPY\n"
        ".venv/bin/pip install --no-index fixture_dep-1.0-py3-none-any.whl",
        ".venv/bin/python -c 'import fixture_dep; print(fixture_dep.value)'",
    ]
    for command in commands:
        result = run(project, command)
        assert result["returncode"] == 0, result
    assert result["stdout"] == "31\n"
    result = run(project, "mkdir -p fixturedep/R library\n"
        "printf 'Package: fixturedep\\nVersion: 1.0\\nTitle: Fixture\\nDescription: Local fixture.\\nAuthor: Test\\nMaintainer: Test <test@example.invalid>\\nLicense: MIT\\n' > fixturedep/DESCRIPTION\n"
        "echo 'export(value)' > fixturedep/NAMESPACE\n"
        "echo 'value <- function() 37L' > fixturedep/R/value.R\n"
        "R CMD INSTALL --library=/work/library fixturedep", "r")
    assert result["returncode"] == 0, result
    result = run(project_factory(), "Rscript --vanilla -e \"library(fixturedep, lib.loc='/work/library'); cat(value())\"", "r")
    assert result["returncode"] == 0 and result["stdout"] == "37", result


@pytest.mark.parametrize("mode", ["exit", "timeout", "overflow"])
def test_vm_lifetime_includes_detached_children(project_factory, mode):
    project = project_factory()
    child = ("import pathlib, time\npathlib.Path('child-ready').touch()\n"
             "while not pathlib.Path('after-receipt').exists(): time.sleep(0.01)\n"
             "pathlib.Path('late-write').write_text('escaped')\n")
    command = ("python - <<'PY'\nimport pathlib, subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', {child!r}], start_new_session=True, "
        "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        "while not pathlib.Path('child-ready').exists(): time.sleep(0.01)\n"
        "print('child started', flush=True)\n"
        + {"exit": "", "timeout": "time.sleep(60)\n",
           "overflow": "while True: print('x' * 10000, flush=True)\n"}[mode] + "PY")
    result = run(project, command)
    assert result["vm_deleted"]
    assert result["timed_out"] == (mode == "timeout")
    assert result["output_truncated"] == (mode == "overflow")
    assert "child started" in result["stdout"]
    assert len(result["stdout"].encode()) + len(result["stderr"].encode()) <= 64000
    checked = run(project, "test -e child-ready && touch after-receipt && sleep 0.5 && test ! -e late-write")
    assert checked["returncode"] == 0, checked


def test_volume_capacity_is_enforced_and_mutation_detected(project_factory):
    project = project_factory()
    result = run(project, "dd if=/dev/zero of=large bs=1048576 count=160")
    assert result["returncode"] != 0 and "No space left" in result["stderr"], result
    assert run(project, "rm large")["returncode"] == 0
    state = json.loads(project.state_path.read_text())
    path = project._volume_path(state)
    with path.open("r+b") as stream:
        first = stream.read(1)
        stream.seek(0)
        stream.write(bytes([first[0] ^ 1]))
    with pytest.raises(ValueError, match="outside its recorded command lineage"):
        run(project, "echo must-not-run")


@pytest.mark.parametrize("after_seal", [False, True])
def test_interruption_never_replays_command(project_factory, monkeypatch, after_seal):
    project = project_factory()
    assert run(project, "echo start")["returncode"] == 0
    original_seal = project._seal
    original_write = module._write_json

    def fail_seal(*args, **kwargs):
        raise OSError("synthetic interruption before receipt")

    def fail_state(path, value):
        if path == project.state_path and "pending" not in value:
            raise OSError("synthetic interruption after receipt")
        original_write(path, value)

    with monkeypatch.context() as scoped:
        if after_seal:
            scoped.setattr(module, "_write_json", fail_state)
        else:
            scoped.setattr(project, "_seal", fail_seal)
        with pytest.raises(OSError, match="synthetic interruption"):
            run(project, "echo once >> counter")
    project._seal = original_seal
    recovered = run(project_factory(), "echo forbidden >> counter",
                    source_handle="unavailable-new-source", revision="unavailable")
    assert recovered["new_command_executed"] is False
    assert recovered["recovered_pending_command"] is True
    assert recovered["interrupted"] == (not after_seal)
    assert run(project, "cat counter")["stdout"] == "once\n"


def test_untrusted_tool_arguments_fail_before_execution(project_factory):
    project = project_factory()
    for args in [{"environment": [], "command": "true"},
                 {"environment": "python", "command": "true", "source_handle": []},
                 {"environment": "python", "command": "true", "host_path": "/"}]:
        with pytest.raises(ClientToolInputError):
            project.execute(args)
    assert not project.state_path.exists()


def test_upstream_rounding_cannot_exceed_operator_disk_limit(project_factory):
    project = project_factory()
    project.config["volume_bytes"] = 67108864
    with pytest.raises(ValueError, match="allocated volume exceeds"):
        run(project, "echo must-not-run")
    assert not list(project.root.glob("command-*"))


def test_acquired_repository_is_selected_readonly_and_exact(project_factory, discovered_repository):
    fixture = discovered_repository
    discovery, handle, revision = (fixture[key] for key in ("discovery", "handle", "revision"))
    project = project_factory(source_resolver=discovery.acquired_repository_snapshot)
    with pytest.raises(ClientToolInputError):
        run(project, "true", source_handle=handle, revision=revision)
    discovery.search("fixture", source_kind="repository")
    discovery.read(handle)
    with pytest.raises(ClientToolInputError, match="acquire this exact"):
        run(project, "true", source_handle=handle, revision=revision)
    discovery.acquire_repository(handle, revision=revision)
    snapshot = discovery.acquired_repository_snapshot(handle, revision)
    result = run(project, "cp -R /source/. /work/; python -c 'from pkg.method import marker; print(marker())'",
                 source_handle=handle, revision=revision)
    assert result["returncode"] == 0 and result["stdout"] == "17\n", result
    result = run(project, "echo changed >> /source/README.md", source_handle=handle, revision=revision)
    assert result["returncode"] != 0 and "Read-only" in result["stderr"], result
    assert snapshot.identity_errors() == []
    (snapshot.source_root / "unlisted-secret").write_text("must not mount")
    with pytest.raises(ValueError, match="unlisted"):
        run(project, "true", source_handle=handle, revision=revision)


def test_native_theory_tool_observation_is_checkpoint_progress(project_factory, tmp_path):
    from ai_statistician.model_backend import ClientToolCall
    from ai_statistician.theory_workspace import (
        THEORY_WORKSPACE_PROGRESS_TOOL, TheoryWorkspaceProgressError,
        load_theory_progress_checkpoint_state,
    )
    from test_theory_workspace import ScriptedTheoryWorkspaceBackend, _response, _run_workspace

    backend = ScriptedTheoryWorkspaceBackend([
        _response(ClientToolCall(call_id="execute", name=module.NATIVE_PROJECT_TOOL,
            input={"environment": "python", "command": "printf raw-feedback; exit 3"})),
        _response(ClientToolCall(call_id="checkpoint", name=THEORY_WORKSPACE_PROGRESS_TOOL,
            input={"summary": "Observed native command failure.", "evidence_refs": ["native command stderr"],
                   "next_step": "Use the raw feedback to choose the next command."})),
    ])
    with pytest.raises(TheoryWorkspaceProgressError) as exc:
        _run_workspace(backend, workspace_dir=tmp_path / "theory", require_document_authority=True,
                       max_turns=2, max_tool_calls=2)
    checkpoint = exc.value.progress_checkpoint
    assert module.NATIVE_PROJECT_TOOL in {tool.name for tool in backend.requests[0].tools}
    assert "raw-feedback" in str(backend.requests[1].messages)
    assert checkpoint["native_project_refs"]
    assert checkpoint["progress"]["phase_observation_refs"][0]["state_field"] == "native_project_refs"
    load_theory_progress_checkpoint_state(checkpoint, question_id="q1")
    assert not checkpoint["kernel_verified"]


def test_native_scientific_tool_does_not_accept_or_release_source(project_factory, tmp_path):
    from ai_statistician.model_backend import ClientToolCall, DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    from ai_statistician.packet_validation import PacketValidationError
    from ai_statistician.scientific_code_workspace import run_scientific_code_workspace
    from test_scientific_code_workspace import ScriptedScientificBackend, _response

    backend = ScriptedScientificBackend([
        _response(ClientToolCall(call_id="run1", name=module.NATIVE_PROJECT_TOOL,
            input={"environment": "python", "command": "echo owner-source > result"})),
        _response(ClientToolCall(call_id="run2", name=module.NATIVE_PROJECT_TOOL,
            input={"environment": "python", "command": "cat result"})),
    ])
    with pytest.raises(PacketValidationError) as exc:
        run_scientific_code_workspace(
            provider=backend, system_prompt="Use your project.", user_prompt="Inspect native output.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL, model_tier="haiku", temperature=0,
            max_tokens=1200, max_turns=2, max_no_progress_turns=2, artifact_id="synthetic:project",
            initial_code_draft=None, initial_check_result={"accepted": False},
            check_candidate=lambda _: pytest.fail("native execution must not call source acceptance"),
            workspace_operation="initial_authoring", session_dir=tmp_path / "scientific",
        )
    checkpoint = exc.value.recovery_checkpoint
    assert checkpoint["checks"] == 0 and checkpoint["source_updates"] == 0
    assert checkpoint["current_source_executed"] is False
    assert len(checkpoint["research_source_refs"]) == 2
    assert all(row["tool"] == module.NATIVE_PROJECT_TOOL for row in checkpoint["research_source_refs"])
    assert "owner-source" in str(backend.requests[1].messages)

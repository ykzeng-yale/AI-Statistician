"""Explicit, offline qualification of Apple's OCI/VM executor, not a product backend."""
from __future__ import annotations

import hashlib
import json
import os
import selectors
import subprocess
import time
import uuid
import zipfile
from pathlib import Path

import pytest


PYTHON_IMAGE = "docker.io/library/python@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2"
R_IMAGE = "docker.io/library/r-base@sha256:41d5564375009abf74a63987fd7fb9b44c90b1580b310be10ef973abe92496c3"


@pytest.fixture
def oci(tmp_path):
    executable = os.environ.get("AI_STATISTICIAN_TEST_APPLE_CONTAINER")
    if not executable:
        pytest.skip("set AI_STATISTICIAN_TEST_APPLE_CONTAINER for explicit native VM qualification")
    executable = str(Path(executable).resolve(strict=True))
    environment = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(tmp_path), "LANG": "en_US.UTF-8"}

    def control(*args, **kwargs):
        return subprocess.run([executable, *args], env=environment, capture_output=True, timeout=45, **kwargs)

    status = json.loads(control("system", "status", "--format", "json", check=True).stdout)
    assert status["client"]["version"] == status["server"]["version"] == "1.4.1"
    assert status["client"]["commit"] == status["server"]["commit"] == "9a8917ca2da5cd6ba059b9ba5ca5a74892e9bb7d"
    control("image", "inspect", PYTHON_IMAGE, check=True)
    return executable, environment, control


def run_oci(oci, project, output, argv, *, image=PYTHON_IMAGE, timeout=30, output_limit=1_000_000):
    """Reuse upstream VM deletion for lifetime containment; never infer command semantics."""
    executable, environment, control = oci
    output.mkdir()
    name = "ais-qualification-" + uuid.uuid4().hex
    command = [
        executable, "run", "--name", name, "--network", "none", "--no-dns",
        "--read-only", "--cap-drop", "ALL", "--cpus", "1", "--memory", "512M",
        "--uid", str(os.getuid()), "--gid", str(os.getgid()),
        "--tmpfs", "/tmp", "--env", "HOME=/tmp", "--env", "TMPDIR=/tmp",
        "--mount", f"type=bind,source={project.resolve()},target=/work",
        "--workdir", "/work", "--progress", "none", "--platform", "linux/arm64",
        "--entrypoint", argv[0], image, *argv[1:],
    ]
    control("image", "inspect", image, check=True)
    started = time.monotonic()
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    timed_out = truncated = False
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        with selectors.DefaultSelector() as selector:
            for label in streams:
                pipe = getattr(process, label)
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, label)
            while selector.get_map():
                if time.monotonic() - started >= timeout:
                    timed_out = True
                    break
                for key, _ in selector.select(timeout=0.05):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    remaining = output_limit - sum(map(len, streams.values()))
                    streams[key.data].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated = True
                        break
                if truncated:
                    break
    finally:
        # A saturated, unread client pipe can block upstream shutdown. Closing
        # our read ends cancels that output consumer without buffering more data.
        process.stdout.close()
        process.stderr.close()
        # Unlike killing a host process group, upstream delete shuts down the
        # entire VM, including detached guest processes. Failure yields no receipt.
        try:
            deleted = control("delete", "--force", name, check=True)
            assert deleted.stdout.strip() == name.encode()
            containers = json.loads(control("list", "--all", "--format", "json", check=True).stdout)
            assert all(row.get("id") != name for row in containers)
        finally:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
    receipt = {
        "argv": argv, "image": image, "container": name, "container_deleted": True,
        "returncode": process.returncode, "timed_out": timed_out, "output_truncated": truncated,
        "elapsed_seconds": time.monotonic() - started,
        "evidence_status": "NATIVE_VM_QUALIFICATION_NOT_RESEARCH_REPLICATION_OR_PROOF",
        **{name: bytes(raw).decode("utf-8", errors="replace") for name, raw in streams.items()},
        "stream_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in streams.items()},
    }
    for name, raw in streams.items():
        (output / f"{name}.txt").write_bytes(raw)
    (output / "receipt.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def test_oci_isolated_files_network_environment_and_raw_errors(oci, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    secret = tmp_path / "private.txt"
    secret.write_text("synthetic-host-secret")
    (project / "escape").symlink_to(secret)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-host-credential")
    source = (
        "import os, pathlib, socket, sys\n"
        "assert 'ANTHROPIC_API_KEY' not in os.environ\n"
        "assert 'SSH_AUTH_SOCK' not in os.environ\n"
        f"assert not pathlib.Path({str(secret)!r}).exists()\n"
        "assert not pathlib.Path('escape').exists()\n"
        "assert sorted(os.listdir('/sys/class/net')) == ['lo']\n"
        "try: socket.create_connection(('1.1.1.1', 443), timeout=1)\n"
        "except OSError: print('network denied')\n"
        "else: raise AssertionError('network reachable')\n"
        "try: pathlib.Path('/etc/host-write').write_text('changed')\n"
        "except OSError: print('root read-only')\n"
        "else: raise AssertionError('root writable')\n"
        "pathlib.Path('result.txt').write_text('source-owned output')\n"
        "print('opaque raw error', file=sys.stderr)\n"
        "sys.exit(23)\n"
    )
    result = run_oci(oci, project, tmp_path / "run", ["python", "-c", source])
    assert result["returncode"] == 23, result
    assert result["stdout"] == "network denied\nroot read-only\n", result
    assert result["stderr"] == "opaque raw error\n", result
    assert secret.read_text() == "synthetic-host-secret"
    assert (project / "result.txt").read_text() == "source-owned output"


def test_oci_prepare_and_reuse_offline_python_environment(oci, tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    wheel = project / "fixture_dep-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for path, source in {
            "fixture_dep.py": "value = 31\n",
            "fixture_dep-1.0.dist-info/METADATA": "Metadata-Version: 2.1\nName: fixture-dep\nVersion: 1.0\n",
            "fixture_dep-1.0.dist-info/WHEEL": "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            "fixture_dep-1.0.dist-info/RECORD": "",
        }.items():
            archive.writestr(path, source)
    for index, argv in enumerate([
        ["python", "-m", "venv", "--copies", ".venv"],
        ["/work/.venv/bin/python", "-m", "pip", "install", "--no-index", wheel.name],
        ["/work/.venv/bin/python", "-c", "import fixture_dep; print(fixture_dep.value)"],
    ]):
        result = run_oci(oci, project, tmp_path / f"run-{index}", argv)
        assert result["returncode"] == 0, result
    assert result["stdout"] == "31\n"


def test_oci_prepare_and_reuse_offline_r_environment(oci, tmp_path):
    project = tmp_path / "project"
    package = project / "fixturedep"
    (package / "R").mkdir(parents=True)
    (project / "library").mkdir()
    (package / "DESCRIPTION").write_text(
        "Package: fixturedep\nVersion: 1.0\nTitle: Fixture\nDescription: Local qualification fixture.\n"
        "Author: Test\nMaintainer: Test <test@example.invalid>\nLicense: MIT\n"
    )
    (package / "NAMESPACE").write_text("export(value)\n")
    (package / "R/value.R").write_text("value <- function() 37L\n")
    for index, argv in enumerate([
        ["R", "CMD", "INSTALL", "--library=/work/library", "fixturedep"],
        ["Rscript", "--vanilla", "-e", "library(fixturedep, lib.loc='/work/library'); cat(value(), '\\n')"],
    ]):
        result = run_oci(oci, project, tmp_path / f"run-{index}", argv, image=R_IMAGE)
        assert result["returncode"] == 0, result
    assert result["stdout"].strip() == "37"


@pytest.mark.parametrize("termination", ["parent_exit", "timeout", "output_limit"])
def test_oci_detached_children_cannot_write_after_receipt(oci, tmp_path, termination):
    project = tmp_path / "project"
    project.mkdir()
    child = (
        "import pathlib, time\n"
        "pathlib.Path('child-ready').touch()\n"
        "while not pathlib.Path('after-receipt').exists(): time.sleep(0.01)\n"
        "pathlib.Path('late-write').write_text('still running')\n"
    )
    parent = (
        "import pathlib, subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', {child!r}], start_new_session=True, "
        "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        "while not pathlib.Path('child-ready').exists(): time.sleep(0.01)\n"
        "print('child started', flush=True)\n"
    )
    if termination == "timeout":
        parent += "time.sleep(60)\n"
    elif termination == "output_limit":
        parent += "while True: print('x' * 10000, flush=True)\n"
    result = run_oci(oci, project, tmp_path / "run", ["python", "-c", parent],
                     timeout=8 if termination == "timeout" else 30, output_limit=100_000)
    assert (project / "child-ready").exists(), result
    assert result["timed_out"] is (termination == "timeout"), result
    assert result["output_truncated"] is (termination == "output_limit"), result
    assert len(result["stdout"].encode()) + len(result["stderr"].encode()) <= 100_000
    (project / "after-receipt").touch()
    time.sleep(0.5)
    assert not (project / "late-write").exists(), result

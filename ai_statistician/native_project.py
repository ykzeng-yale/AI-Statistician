"""An explicit offline OCI command tool for retained source-owning workspaces."""
from __future__ import annotations

import hashlib
import json
import os
import re
import selectors
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping

from .client_tool_loop import ClientToolExecutionResult, ClientToolInputError
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition
from .research_source_discovery import ResearchSourceDiscoveryInputError


NATIVE_PROJECT_CONFIG_ENV = "AI_STATISTICIAN_NATIVE_PROJECT_CONFIG"
NATIVE_PROJECT_TOOL = "run_project_command"
_RUNTIME_COMMIT = "9a8917ca2da5cd6ba059b9ba5ca5a74892e9bb7d"


def _file_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def configured_native_project(
    workspace_dir: Path | None, *, owner: str, authorization: str,
    source_resolver: Callable[[str, str], Any] | None = None,
) -> NativeProject | None:
    configured = os.environ.get(NATIVE_PROJECT_CONFIG_ENV, "").strip()
    if not configured:
        return None
    if workspace_dir is None:
        raise ValueError("native project commands require a persistent source workspace")
    return NativeProject(
        config=json.loads(Path(configured).expanduser().read_text(encoding="utf-8")),
        workspace_dir=workspace_dir, owner=owner, authorization=authorization,
        source_resolver=source_resolver,
    )


class NativeProject:
    """One volume and immutable command receipts; scheduling stays in the caller."""

    def __init__(self, *, config: Mapping[str, Any], workspace_dir: Path,
                 owner: str, authorization: str,
                 source_resolver: Callable[[str, str], Any] | None = None) -> None:
        required = {"container_executable", "environments", "cpus", "memory_bytes",
                    "volume_bytes", "timeout_seconds", "max_output_bytes"}
        if (not isinstance(config, Mapping) or set(config) != required
            or not isinstance(config.get("environments"), Mapping)
            or not isinstance(config.get("container_executable"), str)
            or not owner or not authorization):
            raise ValueError("native project requires an exact environment policy and owner identity")
        self.config = dict(config)
        self.executable = Path(config["container_executable"]).expanduser().resolve(strict=True)
        self.images = dict(config["environments"])
        if not self.images or any(
            not isinstance(key, str) or not key or not isinstance(image, str)
            or not re.fullmatch(r"[a-zA-Z0-9./:_-]+@sha256:[0-9a-f]{64}", image)
            for key, image in self.images.items()
        ):
            raise ValueError("native environments must name exact OCI image digests")
        for key in required - {"container_executable", "environments"}:
            if type(config[key]) is not int or config[key] <= 0:
                raise ValueError(f"native project {key} must be a positive integer")
        if config["volume_bytes"] < 1024 * 1024:
            raise ValueError("native project volume must be at least one MiB")
        if os.getuid() == 0:
            raise ValueError("native model commands require a non-root host user")
        base = workspace_dir.resolve()
        if "," in str(base):
            raise ValueError("native bind mount paths cannot contain commas")
        self.root = base / ".native_project" / stable_hash(owner)[:24]
        if base not in self.root.resolve().parents:
            raise ValueError("native project storage escapes the source workspace")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        home = self.root / "control-home"
        home.mkdir(exist_ok=True, mode=0o700)
        self.environment = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                            "HOME": str(home), "LANG": "en_US.UTF-8"}
        self.source_resolver = source_resolver
        status = self._json_control("system", "status", "--format", "json")
        if (status.get("status") != "running" or any(
            status.get(role, {}).get("commit") != _RUNTIME_COMMIT
            or status.get(role, {}).get("version") != "1.4.1"
            for role in ("client", "server")
        )):
            raise ValueError("native project requires the explicitly started, qualified container 1.4.1 service")
        self.app_root = Path(status["paths"]["appRoot"]).resolve()
        self.identity = {
            "owner": owner, "authorization": authorization, "workspace": str(base),
            "policy": self.config, "executable_sha256": _file_sha(self.executable),
            "runtime_commit": _RUNTIME_COMMIT, "app_root": str(self.app_root),
        }
        self.identity_hash = stable_hash(self.identity)
        self.state_path = self.root / "state.json"
        for image in self.images.values():
            self._check_image(image)
        if self.state_path.exists():
            self._state()

    def _control(self, *args: str) -> subprocess.CompletedProcess:
        result = subprocess.run([str(self.executable), *args], env=self.environment,
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=45)
        if result.returncode:
            raise RuntimeError("container " + " ".join(args[:2]) + ": "
                               + result.stderr.decode("utf-8", errors="replace"))
        return result

    def _json_control(self, *args: str) -> Any:
        return json.loads(self._control(*args).stdout)

    def _check_image(self, image: str) -> None:
        rows = self._json_control("image", "inspect", image)
        if len(rows) != 1 or rows[0]["configuration"]["descriptor"]["digest"] != image.split("@", 1)[1]:
            raise ValueError("native project image identity mismatch")

    def descriptor(self) -> dict[str, Any]:
        return {
            "tool": NATIVE_PROJECT_TOOL, "environment_identity": self.identity_hash,
            "environments": self.images, "working_directory": "/work",
            "source_mount": "/source (read-only, only when explicitly selected)",
            "network_access": False, "persistent_project_volume": True,
            "volume_bytes": self.config["volume_bytes"],
            "timeout_seconds": self.config["timeout_seconds"],
            "boundary": "Exploratory commands only; not accepted source, confirmation, replication or proof. "
                        "Use existing authoring and review tools for authoritative artifacts.",
        }

    def tool(self) -> ClientToolDefinition:
        return ClientToolDefinition(
            name=NATIVE_PROJECT_TOOL,
            description="Run your exact shell command in the selected offline Linux environment. "
                        "Read, write, install local dependencies and test in persistent /work. "
                        "An explicitly selected acquired repository is mounted read-only at /source. "
                        "Inspect raw feedback and author the next command yourself. "
                        + json.dumps(self.descriptor(), sort_keys=True),
            input_schema={
                "type": "object", "additionalProperties": False,
                "required": ["environment", "command"],
                "properties": {
                    "environment": {"type": "string", "enum": sorted(self.images)},
                    "command": {"type": "string", "minLength": 1},
                    "source_handle": {"type": "string", "minLength": 1},
                    "revision": {"type": "string", "minLength": 1},
                },
            },
        )

    def _state(self) -> dict[str, Any]:
        if self.state_path.exists():
            state = json.loads(self.state_path.read_text())
            if state.get("identity_hash") != self.identity_hash:
                raise ValueError("native project owner or environment changed")
            return state
        state = {"identity_hash": self.identity_hash, "volume": "ais-project-" + uuid.uuid4().hex,
                 "initialized": False, "last_receipt": None}
        _write_json(self.state_path, state)
        return state

    def _volume_path(self, state: Mapping[str, Any]) -> Path:
        name = state["volume"]
        if not re.fullmatch(r"ais-project-[0-9a-f]{32}", name):
            raise ValueError("native project volume identity is invalid")
        rows = self._json_control("volume", "inspect", name)
        expected = self.app_root / "volumes" / name / "volume.img"
        if (len(rows) != 1 or rows[0]["id"] != name
            or Path(rows[0]["configuration"]["source"]).resolve() != expected
            or rows[0]["configuration"]["sizeInBytes"] != self.config["volume_bytes"]
            or rows[0]["configuration"].get("labels", {}).get("ais.owner") != self.identity_hash):
            raise ValueError("native project volume does not belong to this workspace policy")
        if expected.stat().st_size > self.config["volume_bytes"]:
            raise ValueError("upstream allocated volume exceeds the configured disk limit")
        return expected

    def _stop_and_delete(self, name: str) -> None:
        if not re.fullmatch(r"ais-command-[0-9a-f]{32}", name):
            raise ValueError("native command container identity is invalid")
        rows = self._json_control("list", "--all", "--format", "json")
        owned = [row for row in rows if row["id"] == name]
        if owned:
            if owned[0]["configuration"].get("labels", {}).get("ais.owner") != self.identity_hash:
                raise ValueError("refusing to delete a container owned by another workspace")
            self._control("delete", "--force", name)
        if any(row["id"] == name for row in self._json_control("list", "--all", "--format", "json")):
            raise RuntimeError("native project VM remained after deletion")

    def execute(self, arguments: Mapping[str, Any]) -> ClientToolExecutionResult:
        import fcntl

        if (set(arguments) - {"environment", "command", "source_handle", "revision"}
            or not isinstance(arguments.get("environment"), str)
            or arguments["environment"] not in self.images
            or not isinstance(arguments.get("command"), str) or not arguments["command"].strip()
            or ("source_handle" in arguments) != ("revision" in arguments)
            or any(not isinstance(arguments[key], str) or not arguments[key].strip()
                   for key in ("source_handle", "revision") if key in arguments)):
            raise ClientToolInputError("run_project_command requires an offered environment and command; "
                                       "source_handle and revision must be supplied together")
        with (self.root / "execution.lock").open("a") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("this native project already has an active command") from exc
            state = self._state()
            if state.get("pending"):
                receipt = self._recover(state)
                return ClientToolExecutionResult(content=receipt, is_error=True, state_changed=True,
                                                  observation_key=receipt["receipt_sha256"])
            source = None
            if arguments.get("source_handle"):
                if self.source_resolver is None:
                    raise ClientToolInputError("this workspace has no acquired source provider")
                try:
                    source = self.source_resolver(arguments["source_handle"], arguments["revision"])
                except ResearchSourceDiscoveryInputError as exc:
                    raise ClientToolInputError(str(exc)) from exc
                if "," in str(source.source_root):
                    raise ValueError("native source mount paths cannot contain commas")
                errors = source.identity_errors()
                if errors:
                    raise ValueError("native project source identity changed: " + "; ".join(errors))
                observed = set()
                for directory, folders, files in os.walk(source.source_root, followlinks=False):
                    for name in [*folders, *files]:
                        path = Path(directory) / name
                        if path.is_symlink() or not path.is_dir():
                            observed.add(path.relative_to(source.source_root).as_posix())
                if observed != {document.relative_path for document in source.documents}:
                    raise ValueError("native source tree contains unlisted or missing files")
            if not state["initialized"]:
                self._initialize(state, arguments["environment"])
            previous = self._load_receipt(state["last_receipt"])
            if _file_sha(self._volume_path(state)) != previous["volume_sha256_after"]:
                raise ValueError("native project changed outside its recorded command lineage")
            receipt = self._run(state, arguments, source=source)
            return ClientToolExecutionResult(
                content=receipt, is_error=receipt["returncode"] != 0 or receipt["timed_out"] or receipt["output_truncated"],
                state_changed=True, observation_key=receipt["receipt_sha256"],
            )

    def _initialize(self, state: dict[str, Any], environment: str) -> None:
        existing = self._json_control("volume", "list", "--format", "json")
        if not any(row["id"] == state["volume"] for row in existing):
            self._control("volume", "create", "-s", str(self.config["volume_bytes"]),
                          "--label", "ais.owner=" + self.identity_hash, state["volume"])
        self._volume_path(state)
        # Only the trusted empty-volume initializer receives CHOWN; model commands
        # run without capabilities under the host user's non-root numeric uid.
        receipt = self._run(state, {"environment": environment, "command": ""}, initialize=True)
        if receipt["returncode"] != 0 or receipt["timed_out"] or receipt["output_truncated"]:
            raise RuntimeError("native project volume initialization failed: " + receipt["stderr"])
        state["initialized"] = True
        _write_json(self.state_path, state)

    def _load_receipt(self, reference: Mapping[str, Any]) -> dict[str, Any]:
        path = self.root / reference["path"]
        if self.root not in path.resolve().parents or _file_sha(path) != reference["sha256"]:
            raise ValueError("native command receipt identity changed")
        return json.loads(path.read_text())

    def _seal(self, state: dict[str, Any], request: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
        directory = self.root / request["invocation"]
        streams = {key: (directory / f"{key}.txt").read_bytes() for key in ("stdout", "stderr")}
        receipt = {
            **dict(request), **dict(result), "volume_sha256_after": _file_sha(self._volume_path(state)),
            "vm_deleted": True, "evidence_status": "EXPLORATORY_NATIVE_PROJECT_NOT_ACCEPTANCE_OR_PROOF",
            **{key: raw.decode("utf-8", errors="replace") for key, raw in streams.items()},
            "stream_sha256": {key: hashlib.sha256(raw).hexdigest() for key, raw in streams.items()},
        }
        path = directory / "receipt.json"
        if path.exists():
            # A crash after sealing but before advancing state must adopt that
            # exact receipt, never replay the command or rewrite its outcome.
            sealed = json.loads(path.read_text())
            if (any(sealed.get(key) != value for key, value in request.items())
                or sealed.get("volume_sha256_after") != receipt["volume_sha256_after"]
                or sealed.get("stream_sha256") != receipt["stream_sha256"]):
                raise ValueError("sealed native receipt differs from pending command")
            receipt = sealed
        else:
            _write_json(path, receipt)
        reference = {"path": path.relative_to(self.root).as_posix(), "sha256": _file_sha(path)}
        state["last_receipt"] = reference
        state.pop("pending", None)
        _write_json(self.state_path, state)
        return {**receipt, "receipt_sha256": reference["sha256"], "receipt_path": str(path)}

    def _recover(self, state: dict[str, Any]) -> dict[str, Any]:
        request = state["pending"]
        if (request["identity_hash"] != self.identity_hash
            or not re.fullmatch(r"command-[0-9a-f]{32}", request["invocation"])
            or self.root not in (self.root / request["invocation"]).resolve().parents):
            raise ValueError("interrupted native command belongs to another workspace")
        self._stop_and_delete(request["container"])
        receipt = self._seal(state, request, {
            "returncode": None, "timed_out": False, "output_truncated": False,
            "interrupted": True, "new_command_executed": False,
            "detail": "The previous command was interrupted. Its VM is now stopped; "
                      "the newly requested command was not executed. Inspect this observation before acting.",
        })
        return {**receipt, "new_command_executed": False,
                "recovered_pending_command": True}

    def _run(self, state: dict[str, Any], arguments: Mapping[str, Any], *, source=None,
             initialize: bool = False) -> dict[str, Any]:
        image = self.images[arguments["environment"]]
        self._check_image(image)
        invocation = "command-" + uuid.uuid4().hex
        directory = self.root / invocation
        commands = directory / "input"
        commands.mkdir(parents=True, mode=0o700)
        (commands / "command.sh").write_text(arguments["command"], encoding="utf-8")
        for key in ("stdout", "stderr"):
            (directory / f"{key}.txt").touch(exist_ok=False)
        name = "ais-command-" + uuid.uuid4().hex
        request = {
            "identity_hash": self.identity_hash, "invocation": invocation, "container": name,
            "environment": arguments["environment"], "image": image, "command": arguments["command"],
            "initialization": initialize, "parent_receipt": state["last_receipt"],
            "volume_sha256_before": _file_sha(self._volume_path(state)),
            "source": source.descriptor() if source is not None else None,
        }
        state["pending"] = request
        _write_json(self.state_path, state)
        command = [
            str(self.executable), "run", "--name", name, "--label", "ais.owner=" + self.identity_hash,
            "--network", "none", "--no-dns",
            "--read-only", "--cap-drop", "ALL", "--cpus", str(self.config["cpus"]),
            "--memory", str(self.config["memory_bytes"]), "--uid", "0" if initialize else str(os.getuid()),
            "--gid", "0" if initialize else str(os.getgid()), "--tmpfs", "/tmp",
            "--env", "HOME=/tmp", "--env", "TMPDIR=/tmp", "--progress", "none", "--platform", "linux/arm64",
            "--mount", f"type=volume,source={state['volume']},target=/work", "--workdir", "/work",
        ]
        if initialize:
            command += ["--cap-add", "CHOWN", "--entrypoint", "/bin/chown", image, f"{os.getuid()}:{os.getgid()}", "/work"]
        else:
            command += ["--mount", f"type=bind,source={commands},target=/command,readonly"]
            if source is not None:
                command += ["--mount", f"type=bind,source={source.source_root},target=/source,readonly"]
            command += ["--entrypoint", "/bin/sh", image, "/command/command.sh"]
        started = time.monotonic()
        timed_out = truncated = False
        count = 0
        process = subprocess.Popen(command, env=self.environment, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            with selectors.DefaultSelector() as selector, (directory / "stdout.txt").open("ab", buffering=0) as stdout, (directory / "stderr.txt").open("ab", buffering=0) as stderr:
                for pipe, target in ((process.stdout, stdout), (process.stderr, stderr)):
                    os.set_blocking(pipe.fileno(), False)
                    selector.register(pipe, selectors.EVENT_READ, target)
                while selector.get_map():
                    if time.monotonic() - started >= self.config["timeout_seconds"]:
                        timed_out = True
                        break
                    for key, _ in selector.select(timeout=0.05):
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        remaining = self.config["max_output_bytes"] - count
                        key.data.write(chunk[:remaining])
                        count += min(len(chunk), remaining)
                        if len(chunk) > remaining:
                            truncated = True
                            break
                    if truncated:
                        break
        finally:
            process.stdout.close()
            process.stderr.close()
            try:
                self._stop_and_delete(name)
            finally:
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
        return self._seal(state, request, {
            "returncode": process.returncode, "timed_out": timed_out, "output_truncated": truncated,
            "interrupted": False, "elapsed_seconds": time.monotonic() - started,
        })

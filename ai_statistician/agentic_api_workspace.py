"""File authoring at an upstream stage boundary, without an outer scheduler."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tempfile
from typing import Any, Mapping

from jsonschema import ValidationError, validate

from .client_tool_loop import (
    CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY,
    ClientToolExecutionResult,
    ClientToolInputError,
    ClientToolLoopError,
    apply_model_exact_text_edits,
    model_exact_text_edits_json_schema,
    persist_client_tool_session,
    run_bounded_client_tool_loop,
    workspace_history_tool,
)
from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition, ClientToolTurnRequest
from .research_source_discovery import (
    ResearchSourceDiscoveryInputError, execute_research_source_discovery_client_tool,
    research_source_discovery_client_tools,
)


@dataclass(frozen=True)
class FileGrant:
    name: str
    path: Path
    directory: bool = False
    writable: bool = False


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        if path.exists():
            temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or value == "." or path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ClientToolInputError("Use an exact workspace-relative path without traversal.")
    return path


def author_tools() -> tuple[ClientToolDefinition, ...]:
    def tool(name, description, properties, required, *, terminal=False):
        return ClientToolDefinition(name=name, description=description, terminal=terminal,
            input_schema={"type": "object", "properties": properties,
                          "required": required, "additionalProperties": False})

    path = {"type": "string", "minLength": 1}
    digest = {"type": ["string", "null"], "pattern": "^[a-f0-9]{64}$"}
    return (
        tool("list_files", "List accessible text/source paths, hashes and write permissions.",
             {"prefix": {"type": "string"}, "offset": {"type": "integer", "minimum": 0},
              "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, []),
        tool("read_file", "Read an exact UTF-8 character range. Hash identifies the whole file; next_offset permits continued reading.",
             {"path": path, "offset": {"type": "integer", "minimum": 0},
              "limit": {"type": "integer", "minimum": 1, "maximum": 16000}}, ["path"]),
        tool("search_file", "Find literal text in one accessible UTF-8 file, returning line-addressed matches.",
             {"path": path, "query": {"type": "string", "minLength": 1},
              "start_line": {"type": "integer", "minimum": 1}}, ["path", "query"]),
        tool("write_file", "Write model-authored UTF-8 content. expected_sha256 must match the current file; use null only to create a new file.",
             {"path": path, "content": {"type": "string"}, "expected_sha256": digest},
             ["path", "content", "expected_sha256"]),
        tool("edit_file", "Apply exact model-authored replacements to the identified current file. No runtime content repair.",
             {"path": path, "expected_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
              "edits": model_exact_text_edits_json_schema()}, ["path", "expected_sha256", "edits"]),
        tool("remove_file", "Remove one writable file after verifying its current hash.",
             {"path": path, "expected_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}},
             ["path", "expected_sha256"]),
        tool("finish", "End this authoring session. candidate hands files to the host, not scientific acceptance; gap reports incomplete work.",
             {"disposition": {"enum": ["candidate", "gap"]}, "summary": {"type": "string", "minLength": 1}},
             ["disposition", "summary"], terminal=True),
        workspace_history_tool(),
    )


class FileAuthorWorkspace:
    """Explicit file grants for a source-only author; no shell or evaluator access."""

    instructions = (
        "You author this stage's research files. The supplied task defines the scientific objective. "
        "Use the file tools to read, develop and revise Markdown/LaTeX and source, and finish with candidate "
        "or an honest gap. No fixed derivation length is required. The host owns execution and independent "
        "evaluation after handoff; a submitted file is not proof or scientific acceptance."
    )

    def tools(self) -> tuple[ClientToolDefinition, ...]:
        return author_tools() + self.discovery_tools

    def __init__(self, grants: tuple[FileGrant, ...], *, discovery=None):
        self.discovery = discovery
        self.discovery_tools = research_source_discovery_client_tools(repository_acquisition=True) if discovery else ()
        if not grants or len({grant.name for grant in grants}) != len(grants):
            raise ValueError("File grants must have unique names.")
        for grant in grants:
            _relative(grant.name)
            if grant.path.absolute() != grant.path.resolve():
                raise ValueError("File grant roots and their ancestors must be canonical, without symlinks.")
            for other in grants:
                if grant != other and PurePosixPath(grant.name) in PurePosixPath(other.name).parents:
                    raise ValueError("File grants must not overlap in logical paths.")
        self.grants = tuple(FileGrant(g.name, g.path.resolve(), g.directory, g.writable) for g in grants)
        self.schemas = {tool.name: tool.input_schema for tool in self.tools()}

    def descriptor(self) -> list[dict[str, Any]]:
        return [{"name": g.name, "directory": g.directory, "writable": g.writable} for g in self.grants]

    def _path(self, name: str, *, write=False) -> Path:
        logical = _relative(name)
        for grant in self.grants:
            root = PurePosixPath(grant.name)
            if logical != root and not (grant.directory and root in logical.parents):
                continue
            if write and not grant.writable:
                raise ClientToolInputError("This file grant is read-only.")
            path = grant.path / str(logical.relative_to(root)) if grant.directory else grant.path
            # The model cannot create links with these tools. Reject preexisting aliases too.
            if path.resolve() != path or (path.exists() and path.stat().st_nlink > 1):
                raise ClientToolInputError("Linked paths are not accessible through this file grant.")
            return path
        raise ClientToolInputError("Path is outside the stage's file grants.")

    def files(self, prefix="") -> list[dict[str, Any]]:
        rows = []
        for grant in self.grants:
            paths = sorted(grant.path.rglob("*")) if grant.directory else [grant.path]
            for path in paths:
                if not path.is_file():
                    continue
                name = grant.name + "/" + path.relative_to(grant.path).as_posix() if grant.directory else grant.name
                if not name.startswith(prefix):
                    continue
                try:
                    data = self._path(name).read_bytes()
                except ClientToolInputError:
                    continue
                rows.append({"path": name, "sha256": _digest(data), "bytes": len(data),
                             "mode": stat.S_IMODE(path.stat().st_mode), "writable": grant.writable})
        return rows

    def execute(self, call, context) -> ClientToolExecutionResult:
        print(json.dumps({"event": "file_tool", "turn": context.turn_index, "tool": call.name}), flush=True)
        try:
            validate(dict(call.input), self.schemas[call.name])
            return self._execute(call.name, dict(call.input))
        except (ValidationError, OSError, UnicodeError, ClientToolInputError, ResearchSourceDiscoveryInputError) as exc:
            return ClientToolExecutionResult(
                content={"error": type(exc).__name__, "detail": str(exc)}, is_error=True)

    def _execute(self, name: str, args: dict[str, Any]) -> ClientToolExecutionResult:
        if name in {tool.name for tool in self.discovery_tools}:
            observation, _, is_error = execute_research_source_discovery_client_tool(
                self.discovery, tool_name=name, tool_input=args)
            return ClientToolExecutionResult(content=observation, is_error=is_error)
        if name == "finish":
            payload = {**args, "scientific_acceptance": False}
            return ClientToolExecutionResult(content=payload, terminal=True, terminal_payload=payload)
        if name == "list_files":
            rows = self.files(args.get("prefix", ""))
            start, limit = args.get("offset", 0), args.get("limit", 100)
            end = min(len(rows), start + limit)
            return ClientToolExecutionResult(content={"files": rows[start:end], "total": len(rows),
                "next_offset": end if end < len(rows) else None})
        path = self._path(args["path"], write=name in {"write_file", "edit_file", "remove_file"})
        if name in {"read_file", "search_file"}:
            data = path.read_bytes()
            content = data.decode("utf-8")
            identity = {"path": args["path"], "sha256": _digest(data), "bytes": len(data)}
            if name == "read_file":
                offset, limit = args.get("offset", 0), args.get("limit", 16000)
                if offset > len(content):
                    raise ClientToolInputError("Offset exceeds the file's character count.")
                end = min(len(content), offset + limit)
                return ClientToolExecutionResult(content={**identity, "content": content[offset:end],
                    "offset": offset, "next_offset": end if end < len(content) else None})
            matches = [{"line": i, "text": line} for i, line in enumerate(content.splitlines(), 1)
                       if i >= args.get("start_line", 1) and args["query"] in line]
            return ClientToolExecutionResult(content={**identity, "matches": matches[:20],
                "next_line": matches[20]["line"] if len(matches) > 20 else None})
        previous = path.read_bytes() if path.exists() else None
        if (_digest(previous) if previous is not None else None) != args["expected_sha256"]:
            raise ClientToolInputError("Source hash changed; read the current file before editing.")
        if name == "remove_file":
            path.unlink()
            return ClientToolExecutionResult(content={"removed": args["path"]}, state_changed=True)
        if name == "edit_file":
            if previous is None:
                raise ClientToolInputError("Cannot edit an absent file.")
            content, _ = apply_model_exact_text_edits(previous.decode("utf-8"),
                edits=args["edits"], replacement_key="new_text")
        else:
            content = args["content"]
        data = content.encode("utf-8")
        _atomic_bytes(path, data)
        return ClientToolExecutionResult(content={"path": args["path"], "sha256": _digest(data),
            "bytes": len(data)}, state_changed=data != previous)


def run_file_session(*, backend, workspace: FileAuthorWorkspace, prompt: str,
                    model: str, max_tokens: int, temperature: float, max_turns: int,
                    session_dir: Path, session_id: str, deployment_identity: Mapping[str, Any]):
    """One upstream-owned stage. The caller retains evaluation and scheduling."""
    session_dir.mkdir(parents=True, exist_ok=False)
    identity = {"deployment": dict(deployment_identity),
        "source_discovery": dict(workspace.discovery.descriptor()) if workspace.discovery else None,
        "grants": [
        {**asdict(g), "path": str(g.path)} for g in workspace.grants],
        "inputs": workspace.files(), "prompt_sha256": _digest(prompt.encode("utf-8"))}
    request = ClientToolTurnRequest(
        system_prompt=(workspace.instructions + " "
            "Only the listed logical paths are accessible; do not use absolute paths from the upstream prompt. "
            "Use read_file offsets to continue long files and workspace history for earlier observations.\n"
            + json.dumps(workspace.descriptor())),
        messages=({"role": "user", "content": prompt},), tools=workspace.tools(),
        model=model, max_tokens=max_tokens, temperature=temperature,
        disable_parallel_tool_use=True,
        metadata={CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY: stable_hash(identity)},
    )
    _atomic_bytes(session_dir / "input.json", (json.dumps({"identity": identity, "request": asdict(request)}, indent=2) + "\n").encode())
    latest: dict[str, Any] = {"messages": list(request.messages), "observation_refs": [], "provider_usage": {}}

    def save(record, *, archive=True):
        files = workspace.files()
        state = {"authorization_fingerprint": stable_hash(identity), "files": files}
        record = {**record, "final_files": files, "durable_state_identity": stable_hash(state),
                  "resume_supported": False}
        if archive:
            record["session_ref"] = persist_client_tool_session(
                session_dir=session_dir, session_id=session_id, request=request,
                messages=record["messages"], durable_state_identity=record["durable_state_identity"],
                observation_refs=record.get("observation_refs", ()))
        _atomic_bytes(session_dir / "result.json", (json.dumps(record, indent=2) + "\n").encode())

    def observe(snapshot):
        latest.clear()
        latest.update(snapshot)
        save({**latest, "status": "INCOMPLETE", "reason": "Authoring has not reached a terminal disposition."}, archive=False)

    try:
        result = run_bounded_client_tool_loop(backend=backend, request=request,
            execute_tool=workspace.execute, max_turns=max_turns, max_tool_calls=max_turns,
            max_no_progress_turns=max_turns, session_dir=session_dir, session_id=session_id,
            observe_progress=observe)
        record = asdict(result)
    except ClientToolLoopError as exc:
        record = {"status": "INCOMPLETE", "reason": exc.reason, "messages": exc.messages,
            "history": exc.history, "provider_usage": exc.provider_usage,
            "final_response_metadata": exc.final_response_metadata, "observation_refs": exc.observation_refs}
        save(record)
        raise
    except BaseException as exc:
        save({**latest, "status": "INTERRUPTED" if isinstance(exc, KeyboardInterrupt) else "INCOMPLETE",
              "reason": type(exc).__name__})
        raise
    save({**record, "status": "HANDED_OFF"})
    return result

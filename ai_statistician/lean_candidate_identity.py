from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence


def run_lean_candidate_identity_probe(
    *,
    artifact_path: Path,
    candidate_lean_declaration: str = "",
    lean_project: Path | None = None,
    lean_timeout: int = 30,
    lean_command: Sequence[str] | None = None,
) -> dict[str, object]:
    """Compile a Lean artifact, then ask Lean to resolve its declared identity."""

    timeout_s = max(1, int(lean_timeout or 30))
    project = Path(lean_project) if lean_project is not None else None
    command_prefix = tuple(
        str(value) for value in (lean_command or ()) if str(value).strip()
    )
    if not command_prefix:
        command_prefix = ("lake", "env", "lean") if project else ("lean",)

    def run_lean(path: Path) -> tuple[str, str, str, list[str]]:
        command = [*command_prefix, str(path.resolve())]
        try:
            completed = subprocess.run(
                command,
                cwd=str(project or path.parent),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            return (
                str(int(completed.returncode)),
                completed.stdout.strip(),
                completed.stderr.strip(),
                command,
            )
        except FileNotFoundError as exc:
            return "not_found", "", str(exc), command
        except subprocess.TimeoutExpired as exc:
            return (
                "timeout",
                str(exc.stdout or "").strip(),
                f"timeout after {timeout_s}s: {exc.stderr or ''}".strip(),
                command,
            )
        except OSError as exc:
            return "execution_error", "", f"{type(exc).__name__}: {exc}", command

    source_exit_status, source_stdout, source_stderr, source_command = run_lean(
        artifact_path
    )
    declaration = str(candidate_lean_declaration or "").strip()
    identity_checked = False
    identity_verified = False
    identity_probe_path = ""
    identity_exit_status = ""
    identity_stdout = ""
    identity_stderr = ""
    identity_command: list[str] = []
    if source_exit_status == "0" and declaration:
        identity_checked = True
        probe_path = artifact_path.with_name(
            artifact_path.stem + ".candidate_identity_probe.lean"
        )
        identity_probe_path = str(probe_path)
        try:
            source = artifact_path.read_text(encoding="utf-8")
            probe_path.write_text(
                source.rstrip() + "\n\n#check " + declaration + "\n",
                encoding="utf-8",
            )
            (
                identity_exit_status,
                identity_stdout,
                identity_stderr,
                identity_command,
            ) = run_lean(probe_path)
            identity_verified = identity_exit_status == "0"
        except OSError as exc:
            identity_exit_status = "probe_write_error"
            identity_stderr = str(exc)

    exit_status = source_exit_status
    stdout = source_stdout
    stderr = source_stderr
    if identity_checked and not identity_verified:
        exit_status = identity_exit_status
        stdout = "\n".join(
            value for value in (source_stdout, identity_stdout) if value
        )
        stderr = "\n".join(
            value for value in (source_stderr, identity_stderr) if value
        )
    return {
        "local_lean_attempted": True,
        "local_lean_compiled": exit_status == "0",
        "local_lean_source_compiled": source_exit_status == "0",
        "local_lean_source_exit_status": source_exit_status,
        "local_lean_exit_status": exit_status,
        "local_lean_stdout": stdout[:4000],
        "local_lean_stderr": stderr[:4000],
        "local_lean_command": source_command,
        "local_lean_project": str(project or ""),
        "local_lean_timeout": timeout_s,
        "local_lean_skipped_reason": "",
        "candidate_identity_lean_checked": identity_checked,
        "candidate_identity_lean_verified": identity_verified,
        "candidate_identity_probe_artifact_path": identity_probe_path,
        "candidate_identity_lean_exit_status": identity_exit_status,
        "candidate_identity_lean_stdout": identity_stdout[:4000],
        "candidate_identity_lean_stderr": identity_stderr[:4000],
        "candidate_identity_lean_command": identity_command,
    }

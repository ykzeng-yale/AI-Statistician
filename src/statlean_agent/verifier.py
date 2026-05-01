"""Verifier abstractions for Lean proof attempts."""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from statlean_agent.contracts import LeanTask, ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.rewards import FORBIDDEN_TOKENS, find_forbidden_tokens, scan_policy_tokens


@dataclass(frozen=True)
class StaticVerifier:
    """Fast verifier for policy violations before Lean is invoked."""

    forbidden_tokens: tuple[str, ...] = FORBIDDEN_TOKENS
    allowed_placeholders: tuple[str, ...] = ()

    def check(
        self,
        attempt: ProofAttempt,
        *,
        allowed_placeholders: Iterable[str] | None = None,
    ) -> VerificationReport:
        allowed = self.allowed_placeholders if allowed_placeholders is None else tuple(allowed_placeholders)
        violations = find_forbidden_tokens(
            attempt.lean_code,
            allowed_placeholders=allowed,
            policy_tokens=self.forbidden_tokens,
        )
        observations = scan_policy_tokens(
            attempt.lean_code,
            allowed_placeholders=allowed,
            policy_tokens=self.forbidden_tokens,
        )
        diagnostics = tuple(occurrence.diagnostic for occurrence in observations)

        if violations:
            first = violations[0]
            return VerificationReport(
                task_id=attempt.task_id,
                status=VerificationStatus.REJECTED,
                first_error=f"forbidden token `{first.token}` at line {first.line}, column {first.column}",
                diagnostics=diagnostics,
            )
        return VerificationReport(
            task_id=attempt.task_id,
            status=VerificationStatus.ACCEPTED,
            diagnostics=diagnostics,
        )


@dataclass(frozen=True)
class LakeVerifier:
    """Run a Lean task through `lake env lean` inside a Lake repository."""

    repo_root: Path
    timeout_seconds: int = 60

    def verify_task(self, task: LeanTask) -> VerificationReport:
        source = render_task(task)
        allowed_placeholders = ("sorry",) if task.allowed_sorry else ()
        return self.verify_source(task.task_id, source, allowed_placeholders=allowed_placeholders)

    def verify_source(
        self,
        task_id: str,
        source: str,
        *,
        allowed_placeholders: Iterable[str] = (),
    ) -> VerificationReport:
        static_attempt = ProofAttempt(task_id=task_id, agent_key="verifier", lean_code=source)
        static_report = StaticVerifier().check(static_attempt, allowed_placeholders=allowed_placeholders)
        if static_report.status is not VerificationStatus.ACCEPTED:
            return static_report

        with tempfile.TemporaryDirectory(prefix="statlean-verify-") as tmpdir:
            path = Path(tmpdir) / "Task.lean"
            path.write_text(source, encoding="utf-8")
            try:
                result = subprocess.run(
                    ["lake", "env", "lean", str(path)],
                    cwd=self.repo_root,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except FileNotFoundError:
                return VerificationReport(
                    task_id=task_id,
                    status=VerificationStatus.ERROR,
                    first_error="lake executable not found",
                    diagnostics=static_report.diagnostics + ("lake executable not found",),
                )
            except subprocess.TimeoutExpired:
                return VerificationReport(
                    task_id=task_id,
                    status=VerificationStatus.TIMEOUT,
                    first_error=f"verification timed out after {self.timeout_seconds}s",
                    diagnostics=static_report.diagnostics
                    + (f"verification timed out after {self.timeout_seconds}s",),
                )

        if result.returncode == 0:
            return VerificationReport(
                task_id=task_id,
                status=VerificationStatus.ACCEPTED,
                diagnostics=static_report.diagnostics,
            )
        diagnostics = _process_diagnostics(result.stderr, result.stdout, path)
        return VerificationReport(
            task_id=task_id,
            status=VerificationStatus.REJECTED,
            first_error=_sanitize_diagnostic_path(
                _first_nonempty_line(result.stderr) or _first_nonempty_line(result.stdout),
                path,
            ),
            diagnostics=static_report.diagnostics + diagnostics,
        )


def render_task(task: LeanTask) -> str:
    """Render a Lean task into a standalone Lean source string."""

    imports = "\n".join(f"import {module}" for module in task.imports)
    namespace_open = f"\nnamespace {task.namespace}\n" if task.namespace else "\n"
    namespace_close = f"\nend {task.namespace}\n" if task.namespace else "\n"
    return f"{imports}\n{namespace_open}\n{task.statement}\n{namespace_close}"


def _first_nonempty_line(value: str) -> str | None:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _process_diagnostics(stderr: str, stdout: str, source_path: Path | None = None) -> tuple[str, ...]:
    return tuple(
        _sanitize_diagnostic_path(line.strip(), source_path)
        for line in (stderr + "\n" + stdout).splitlines()
        if line.strip()
    )


def _sanitize_diagnostic_path(line: str | None, source_path: Path | None = None) -> str | None:
    if line is None or source_path is None:
        return line
    return line.replace(str(source_path), "Task.lean")

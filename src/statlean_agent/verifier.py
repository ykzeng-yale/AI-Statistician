"""Verifier abstractions for Lean proof attempts."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from statlean_agent.contracts import LeanTask, ProofAttempt, VerificationReport, VerificationStatus
from statlean_agent.rewards import FORBIDDEN_TOKENS


@dataclass(frozen=True)
class StaticVerifier:
    """Fast verifier for policy violations before Lean is invoked."""

    forbidden_tokens: tuple[str, ...] = FORBIDDEN_TOKENS

    def check(self, attempt: ProofAttempt) -> VerificationReport:
        lowered = attempt.lean_code.lower()
        for token in self.forbidden_tokens:
            if token in lowered:
                return VerificationReport(
                    task_id=attempt.task_id,
                    status=VerificationStatus.REJECTED,
                    first_error=f"forbidden token: {token}",
                    diagnostics=(f"forbidden token `{token}`",),
                )
        return VerificationReport(task_id=attempt.task_id, status=VerificationStatus.ACCEPTED)


@dataclass(frozen=True)
class LakeVerifier:
    """Run a Lean task through `lake env lean` inside a Lake repository."""

    repo_root: Path
    timeout_seconds: int = 60

    def verify_task(self, task: LeanTask) -> VerificationReport:
        source = render_task(task)
        return self.verify_source(task.task_id, source)

    def verify_source(self, task_id: str, source: str) -> VerificationReport:
        static_attempt = ProofAttempt(task_id=task_id, agent_key="verifier", lean_code=source)
        static_report = StaticVerifier().check(static_attempt)
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
                    diagnostics=("lake executable not found",),
                )
            except subprocess.TimeoutExpired:
                return VerificationReport(
                    task_id=task_id,
                    status=VerificationStatus.TIMEOUT,
                    first_error=f"verification timed out after {self.timeout_seconds}s",
                    diagnostics=(f"verification timed out after {self.timeout_seconds}s",),
                )

        if result.returncode == 0:
            return VerificationReport(task_id=task_id, status=VerificationStatus.ACCEPTED)
        return VerificationReport(
            task_id=task_id,
            status=VerificationStatus.REJECTED,
            first_error=_first_nonempty_line(result.stderr) or _first_nonempty_line(result.stdout),
            diagnostics=tuple(line for line in (result.stderr + "\n" + result.stdout).splitlines() if line.strip()),
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

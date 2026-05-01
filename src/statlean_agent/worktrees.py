"""Git worktree management for isolated agent edits."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from statlean_agent.agents import AgentRole
from statlean_agent.contracts import WorktreeAssignment


class WorktreeError(RuntimeError):
    """Raised when git worktree setup fails."""


@dataclass(frozen=True)
class WorktreeManager:
    """Create predictable worktree branches for code-writing agents."""

    repo_root: Path
    worktrees_dir: Path | None = None
    branch_prefix: str = "agent"

    def __post_init__(self) -> None:
        root = self.repo_root.resolve()
        object.__setattr__(self, "repo_root", root)
        if self.worktrees_dir is None:
            object.__setattr__(self, "worktrees_dir", root / ".worktrees")

    def assignment_for(self, agent: AgentRole, base_branch: str = "main") -> WorktreeAssignment:
        slug = _slug(agent.key)
        branch = f"{self.branch_prefix}/{slug}"
        path = str((self.worktrees_dir or self.repo_root / ".worktrees") / slug)
        return WorktreeAssignment(
            agent_key=agent.key,
            branch=branch,
            path=path,
            base_branch=base_branch,
            owns=agent.owns,
        )

    def create(self, agent: AgentRole, base_branch: str = "main", dry_run: bool = False) -> WorktreeAssignment:
        assignment = self.assignment_for(agent, base_branch=base_branch)
        if dry_run:
            return WorktreeAssignment(**{**assignment.__dict__, "dry_run": True})

        Path(assignment.path).parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "git",
            "worktree",
            "add",
            "-B",
            assignment.branch,
            assignment.path,
            assignment.base_branch,
        ]
        result = subprocess.run(cmd, cwd=self.repo_root, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise WorktreeError(result.stderr.strip() or result.stdout.strip())
        return assignment

    def remove(self, assignment: WorktreeAssignment, force: bool = False) -> None:
        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(assignment.path)
        result = subprocess.run(cmd, cwd=self.repo_root, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise WorktreeError(result.stderr.strip() or result.stdout.strip())


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    slug = slug.strip("-")
    if not slug:
        raise ValueError("empty slug")
    return slug


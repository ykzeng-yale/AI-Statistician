"""Command-line interface for local orchestration utilities."""

from __future__ import annotations

import argparse
from pathlib import Path

from statlean_agent.agents import AGENT_REGISTRY, get_agent
from statlean_agent.orchestrator import DEFAULT_WORKFLOW
from statlean_agent.worktrees import WorktreeManager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="statlean")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-agents", help="List configured agents.")
    subparsers.add_parser("workflow", help="Print the default workflow.")

    assign = subparsers.add_parser("assign-worktree", help="Create or preview an agent worktree.")
    assign.add_argument("--agent", required=True, help="Agent key.")
    assign.add_argument("--base", default="main", help="Base branch.")
    assign.add_argument("--repo", default=".", help="Repository root.")
    assign.add_argument("--dry-run", action="store_true", help="Preview without creating worktree.")

    args = parser.parse_args(argv)
    if args.command == "list-agents":
        for agent in AGENT_REGISTRY:
            print(f"{agent.key}: {agent.name}")
        return 0

    if args.command == "workflow":
        for index, stage in enumerate(DEFAULT_WORKFLOW, start=1):
            print(f"{index}. {stage.name}: {', '.join(stage.agents)} -> {stage.output}")
        return 0

    if args.command == "assign-worktree":
        agent = get_agent(args.agent)
        manager = WorktreeManager(Path(args.repo))
        assignment = manager.create(agent, base_branch=args.base, dry_run=args.dry_run)
        print(f"agent={assignment.agent_key}")
        print(f"branch={assignment.branch}")
        print(f"path={assignment.path}")
        print(f"owns={','.join(assignment.owns)}")
        print(f"dry_run={assignment.dry_run}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())


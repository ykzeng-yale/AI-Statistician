"""Command-line interface for local orchestration utilities."""

from __future__ import annotations

import argparse
from pathlib import Path

from statlean_agent.agents import AGENT_REGISTRY, get_agent
from statlean_agent.benchmarks import load_benchmarks, seed_benchmarks
from statlean_agent.contracts import ProofAttempt, VerificationReport
from statlean_agent.evaluation import evaluate_attempts
from statlean_agent.orchestrator import DEFAULT_WORKFLOW
from statlean_agent.retrieval import PremiseRecord, build_premise_index, search_premises
from statlean_agent.serialization import dataclass_from_dict, dumps_json, read_jsonl, write_jsonl
from statlean_agent.training import build_training_manifest
from statlean_agent.verifier import LakeVerifier, render_task
from statlean_agent.worktrees import WorktreeManager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="statlean")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-agents", help="List configured agents.")
    subparsers.add_parser("workflow", help="Print the default workflow.")

    seed = subparsers.add_parser("seed-benchmarks", help="Write seed benchmark tasks.")
    seed.add_argument("--output", default="benchmarks/seeds.jsonl", help="Output JSONL path.")

    list_benchmarks = subparsers.add_parser("list-benchmarks", help="List benchmark tasks.")
    list_benchmarks.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")

    render = subparsers.add_parser("render-task", help="Render one benchmark task as Lean source.")
    render.add_argument("task_id", help="Benchmark task id.")
    render.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")

    verify = subparsers.add_parser("verify-task", help="Verify one benchmark task using local Lake.")
    verify.add_argument("task_id", help="Benchmark task id.")
    verify.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")
    verify.add_argument("--repo", default=".", help="Lake repository root.")
    verify.add_argument("--timeout", type=int, default=60, help="Verification timeout in seconds.")

    verify_all = subparsers.add_parser("verify-benchmarks", help="Verify all benchmark tasks using local Lake.")
    verify_all.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")
    verify_all.add_argument("--output", default="artifacts/verification/reports.jsonl", help="Output JSONL path.")
    verify_all.add_argument("--repo", default=".", help="Lake repository root.")
    verify_all.add_argument("--timeout", type=int, default=60, help="Verification timeout in seconds.")
    verify_all.add_argument("--allow-failures", action="store_true", help="Return success even when tasks fail.")

    eval_attempts = subparsers.add_parser("eval-attempts", help="Evaluate proof attempts and reports.")
    eval_attempts.add_argument("--attempts", required=True, help="ProofAttempt JSONL path.")
    eval_attempts.add_argument("--reports", required=True, help="VerificationReport JSONL path.")

    index_premises = subparsers.add_parser("index-premises", help="Index local Lean declarations.")
    index_premises.add_argument("--root", default=".", help="Repository root.")
    index_premises.add_argument("--source-dir", default="StatInference", help="Lean source directory.")
    index_premises.add_argument("--output", default="artifacts/premise_index/local.jsonl", help="Output JSONL path.")

    search = subparsers.add_parser("search-premises", help="Search a premise index.")
    search.add_argument("query", help="Search query.")
    search.add_argument("--index", default="artifacts/premise_index/local.jsonl", help="Premise index JSONL.")
    search.add_argument("--top-k", type=int, default=8, help="Number of matches.")

    train_manifest = subparsers.add_parser("build-training-manifest", help="Build SFT/DPO/GRPO manifest.")
    train_manifest.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="Benchmark JSONL path.")
    train_manifest.add_argument("--output", default="artifacts/training/manifest.json", help="Manifest JSON path.")
    train_manifest.add_argument("--run-id", default="local-seed", help="Run id.")
    train_manifest.add_argument("--base-model", default="unspecified-lean-prover", help="Base model name.")

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

    if args.command == "seed-benchmarks":
        path = Path(args.output)
        seed_benchmarks(path)
        print(f"wrote {path}")
        return 0

    if args.command == "list-benchmarks":
        tasks = load_benchmarks(Path(args.input))
        for task in tasks:
            print(f"{task.task_id}\t{task.task_type.value}\t{task.split.value}\t{','.join(task.domain_tags)}")
        return 0

    if args.command == "render-task":
        task = _find_task(Path(args.input), args.task_id)
        print(render_task(task.lean_task))
        return 0

    if args.command == "verify-task":
        task = _find_task(Path(args.input), args.task_id)
        verifier = LakeVerifier(Path(args.repo), timeout_seconds=args.timeout)
        report = verifier.verify_task(task.lean_task)
        print(f"status={report.status.value}")
        if report.first_error:
            print(f"first_error={report.first_error}")
        for diagnostic in report.diagnostics:
            print(diagnostic)
        return 0 if report.status.value == "accepted" else 1

    if args.command == "verify-benchmarks":
        tasks = load_benchmarks(Path(args.input))
        verifier = LakeVerifier(Path(args.repo), timeout_seconds=args.timeout)
        reports = [verifier.verify_task(task.lean_task) for task in tasks]
        write_jsonl(Path(args.output), reports)
        accepted = sum(1 for report in reports if report.status.value == "accepted")
        print(f"verified={len(reports)} accepted={accepted} output={args.output}")
        if accepted == len(reports) or args.allow_failures:
            return 0
        return 1

    if args.command == "eval-attempts":
        attempts = tuple(dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.attempts)))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        print(dumps_json(evaluate_attempts(attempts, reports)))
        return 0

    if args.command == "index-premises":
        records = build_premise_index(Path(args.root), source_dir=args.source_dir)
        write_jsonl(Path(args.output), list(records))
        print(f"indexed={len(records)} output={args.output}")
        return 0

    if args.command == "search-premises":
        records = tuple(dataclass_from_dict(PremiseRecord, record) for record in read_jsonl(Path(args.index)))
        for premise in search_premises(records, args.query, top_k=args.top_k):
            print(f"{premise.name}\t{premise.kind}\t{premise.module}:{premise.line}")
        return 0

    if args.command == "build-training-manifest":
        tasks = load_benchmarks(Path(args.benchmarks))
        manifest = build_training_manifest(tasks, run_id=args.run_id, base_model=args.base_model)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(manifest) + "\n", encoding="utf-8")
        print(f"wrote {output}")
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


def _find_task(path: Path, task_id: str):
    tasks = load_benchmarks(path)
    for task in tasks:
        if task.task_id == task_id:
            return task
    raise SystemExit(f"unknown task id: {task_id}")


if __name__ == "__main__":
    raise SystemExit(main())

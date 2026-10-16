"""Native source-only investigation participant for the pinned upstream patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_statistician.agentic_api_workspace import FileAuthorWorkspace, FileGrant, run_file_session
from ai_statistician.agentic_scientific_review import run_scientific_review
from ai_statistician.local_model_backend import LocalChatGeneratorBackend


def load_config(path: Path, *, model: str) -> tuple[dict, dict]:
    config = json.loads(path.read_text())
    required = {"model", "base_url", "max_tokens", "temperature", "timeout_seconds",
                "max_turns", "deployment_ref"}
    if not isinstance(config, dict) or set(config) != required:
        raise ValueError("Supply exactly the documented native API configuration fields.")
    if config["model"] != model:
        raise ValueError("Stage model differs from the frozen API model; no substitution allowed.")
    for key in ("max_tokens", "max_turns", "timeout_seconds"):
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError(f"{key} must be a positive integer.")
    if type(config["temperature"]) not in (int, float) or not math.isfinite(config["temperature"]) or config["temperature"] < 0:
        raise ValueError("temperature must be finite and nonnegative.")
    ref = config["deployment_ref"]
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise ValueError("deployment_ref requires path and sha256.")
    receipt_path = Path(ref["path"]).expanduser().resolve(strict=True)
    receipt = receipt_path.read_bytes()
    if hashlib.sha256(receipt).hexdigest() != ref["sha256"]:
        raise ValueError("Deployment receipt hash mismatch.")
    return config, {"config": config, "deployment_ref": {**ref, "path": str(receipt_path)},
                    "scope": "Operator-declared pinned deployment; response model identity checked on every request."}


def campaign_history_grants(results: Path | None, *, current: Path) -> tuple[FileGrant, ...]:
    """Expose prior author source and search observations, never evaluator source."""
    if results is None:
        return ()
    results = results.resolve()
    grants = [FileGrant("history/" + name, results / name) for name in
              ("memory.md", "memory.jsonl", "conclusions.md", "attempts_history.jsonl", "ideas_history.jsonl")
              if (results / name).is_file()]
    for attempt in sorted((results / "ideas").glob("*")):
        if not attempt.is_dir() or attempt.resolve() == current.resolve():
            continue
        prefix = "history/" + attempt.relative_to(results).as_posix()
        for name in ("active_idea.json", "active_rubrics.json", ".local-api/session/result.json"):
            if (attempt / name).is_file():
                grants.append(FileGrant(prefix + "/" + name, attempt / name))
        for program in sorted(attempt.glob("program_[0-9]*")):
            for name in ("src", "program_spec.toml", "metrics.json", "correct.json", "rubric_status.json",
                         "evaluation_manifest.json", "harness_evaluate_stdout.log", "harness_evaluate_stderr.log",
                         "scientific_review.md", "scientific_review.json",
                         "scientific_review_stdout.log", "scientific_review_stderr.log"):
                path = program / name
                if path.exists():
                    grants.append(FileGrant(prefix + "/" + program.name + "/" + name, path, directory=name == "src"))
    return tuple(grants)


def posthoc_workspace(root: Path) -> FileAuthorWorkspace:
    """Interpret the upstream host's verified public bundle, without evaluator access."""
    root = root.resolve()
    spec = json.loads((root / "analysis_spec.json").read_text())
    outputs = spec["expected_outputs"]
    if not isinstance(outputs, list) or not all(isinstance(name, str) for name in outputs):
        raise ValueError("Native posthoc expected_outputs must be an explicit file list.")
    required = {"analysis_summary.md", "interestingness_rubric.json", "analysis_manifest.json", "rubric_status.json"}
    outputs = required | set(outputs)
    if any(Path(name).parts[:1] == ("task_bundle",) or
           any(part.startswith(".") or any(char in part for char in "*?[]")
               for part in Path(name).parts) for name in outputs):
        raise ValueError("Native posthoc output paths must be explicit, non-hidden files.")
    grants = [FileGrant(name, root / name) for name in (
        "analysis_spec.json", "rubric_contract.json", "target_rubrics.json",
        "task_bundle/task.md", "task_bundle/original_task.md", "task_bundle/evidence_manifest.json",
        "task_bundle/program_0/program_spec.toml",
    ) if (root / name).is_file()]
    grants.extend((FileGrant("task_bundle/evidence", root / "task_bundle/evidence", directory=True),
                   FileGrant("task_bundle/resources/search", root / "task_bundle/resources/search", directory=True),
                   FileGrant("task_bundle/program_0/src", root / "task_bundle/program_0/src", directory=True)))
    grants.extend(FileGrant(name, root / name, writable=True) for name in sorted(outputs))
    workspace = FileAuthorWorkspace(tuple(grants))
    workspace.instructions = (
        "You interpret the host's supplied scientific evidence and author the requested report files. "
        "Read the task, analysis spec, source and actual result tables. Evidence is read-only. "
        "There is no evaluator or execution tool in this session: do not claim new calculations, "
        "plots, simulations or proof ran. Interpret existing summaries, preserve failures and uncertainty, "
        "and distinguish source review from numerical evidence. Use Markdown/LaTeX for substantive "
        "reasoning; the required small JSON files are upstream artifact bookkeeping, not certification. "
        "Finish with candidate or an honest gap. Self-rubrics do not independently validate the report."
    )
    return workspace


def stage_workspace(root: Path, source: Path, *, stage="research", results: Path | None = None) -> FileAuthorWorkspace:
    root, source = root.resolve(), source.resolve()
    shared = (
        FileGrant("skills", root / ".local-api/skills", directory=True),
        FileGrant("sources", source / "resources/search", directory=True),
        *campaign_history_grants(results, current=root),
    )
    if stage == "idea":
        return FileAuthorWorkspace((
            FileGrant("task.md", source / "task.md"),
            FileGrant("task_requirements.json", source / "target_rubrics.json"),
            FileGrant("program_0", source / "program_0", directory=True),
            FileGrant("idea_bundle.json", root / "idea_bundle.json", writable=True),
            FileGrant("target_rubrics.json", root / "target_rubrics.json", writable=True),
            *shared,
        ))
    if stage != "research":
        raise ValueError("Unknown native API stage.")
    grants = [
        FileGrant(name, root / name) for name in
        ("task.md", "active_idea.json", "active_rubrics.json") if (root / name).is_file()
    ]
    grants.extend((
        FileGrant("program_0", root / "program_0", directory=True),
        FileGrant("program_1/src", root / "program_1/src", directory=True, writable=True),
        FileGrant("program_1/program_spec.toml", root / "program_1/program_spec.toml", writable=True),
        FileGrant("memory.md", root / "memory.md", writable=True),
        *shared,
    ))
    workspace = FileAuthorWorkspace(tuple(grants))
    specification = tomllib.loads(workspace._path("program_0/program_spec.toml").read_text())
    if specification.get("schema_version") != 1 or specification["code_root"] != "src":
        raise ValueError("The pinned upstream schema_version=1 requires code_root='src'.")
    return workspace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--stage", choices=("idea", "research", "review", "posthoc"), default="research")
    parser.add_argument("--program-dir", type=Path)
    parser.add_argument("--task-dir", type=Path)
    parser.add_argument("--rubrics-file", type=Path)
    args = parser.parse_args()
    if args.stage == "review":
        if not all((args.program_dir, args.task_dir, args.rubrics_file)) or args.prompt_file:
            parser.error("Review requires program-dir, task-dir and rubrics-file; its prompt is fixed by the integration.")
    elif not args.prompt_file or any((args.program_dir, args.task_dir, args.rubrics_file)):
        parser.error("Author stages require only prompt-file and model.")
    config, identity = load_config(Path(os.environ["AI_STATISTICIAN_API_CONFIG"]), model=args.model)
    root = Path.cwd().resolve()
    backend = LocalChatGeneratorBackend(base_url=config["base_url"], timeout_s=config["timeout_seconds"])
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"Received signal {signum}")

    previous_handler = signal.signal(signal.SIGTERM, interrupted)
    try:
        if args.stage == "review":
            prompt = Path(__file__).resolve().parents[1] / "integrations/agentic-scientist/prompts/scientific-review.md"
            review = run_scientific_review(
                backend=backend, program=args.program_dir, task=args.task_dir,
                rubrics_file=args.rubrics_file,
                sources=Path(os.environ.get("TASK_SOURCE_DIR", str(args.task_dir))),
                config=config, deployment_identity=identity, prompt=prompt.read_text(),
            )
            print(json.dumps({"event": "api_review_terminal", "model": review["model"],
                              "verdicts": review["verdicts"], "proof_evidence": False}), flush=True)
            return 0
        results = Path(os.environ["AI_STATISTICIAN_CAMPAIGN_RESULTS"]) if os.environ.get("AI_STATISTICIAN_CAMPAIGN_RESULTS") else None
        workspace = (posthoc_workspace(root) if args.stage == "posthoc" else
                     stage_workspace(root, Path(os.environ["TASK_SOURCE_DIR"]), stage=args.stage, results=results))
        prompt = args.prompt_file.read_text()
        if args.stage == "idea":
            prompt = ("Native API stage contract: write idea_bundle.json and target_rubrics.json. "
                      "Keep author notes in notes_for_agent; the host owns global memory bookkeeping. "
                      "Use only granted logical paths, including history for prior source and raw observations. "
                      "task_requirements.json, when present, is the operator's fixed acceptance contract.\n\n"
                      + prompt)
        result = run_file_session(
            backend=backend, workspace=workspace, prompt=prompt,
            model=args.model, max_tokens=config["max_tokens"], temperature=config["temperature"],
            max_turns=config["max_turns"], session_dir=root / ".local-api/session",
            session_id=(f"posthoc_{root.name}" if args.stage == "posthoc" else
                        f"idea_{os.environ['CYCLE_INDEX']}" if args.stage == "idea" else os.environ["ATTEMPT_ID"]),
            deployment_identity={**identity, "stage": args.stage},
        )
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    print(json.dumps({"event": "api_author_terminal", "provider": result.provider,
        "model": result.model, "provider_usage": dict(result.provider_usage),
        "disposition": result.terminal_payload["disposition"], "scientific_acceptance": False}), flush=True)
    return 0 if result.terminal_payload["disposition"] == "candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())

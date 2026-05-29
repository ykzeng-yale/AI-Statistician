from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .research_source_inventory import AUTOFORM_BOT_ROOT


@dataclass(frozen=True)
class AutoformHarnessProfile:
    root: str
    exists: bool
    git_commit: str
    remote_url: str
    has_statement_extraction: bool
    has_lean_eval: bool
    has_dependency_graph_eval: bool
    has_lean_proof_checker: bool
    has_lean_repl_tool: bool
    has_native_lsp_tool: bool
    has_lean_skill_docs: bool
    has_multi_agent_bot: bool
    has_visualizer: bool
    usage_policy: str
    command_templates: tuple[str, ...]
    reusable_modules: tuple[str, ...]


def build_autoform_harness_profile(root: Path = AUTOFORM_BOT_ROOT) -> AutoformHarnessProfile:
    """Detect the local autoform-bot harness and expose safe reuse hooks.

    The harness is used as an integration target for statement extraction,
    Lean checking, dependency-graph evaluation, proof-checker wrappers,
    REPL/LSP tooling, Lean proof-pattern skill docs, and trace visualization.
    This profile is intentionally an execution/reference integration artifact;
    training exporters separately decide which source payloads to serialize.
    """

    root = root.expanduser()
    exists = root.exists()
    modules = (
        "autoform.statement_extraction",
        "autoform.eval.lean_checks",
        "autoform.eval.compilation_grader",
        "autoform.eval.dependency_graph.builder",
        "autoform.eval.dependency_graph.tagger",
        "tools.execution.lean.repl",
        "tools.execution.lean.lsp",
        "tools.execution.lean.native_lsp",
        "tools.execution.lean.proof_checker",
        "core.agent.loop",
        "core.trace",
    )
    command_templates = (
        "python -m autoform.statement_extraction run --book-dir <book_dir> --output <book_dir>/targets.yaml",
        "python -m autoform.bot.main run --config <config.yaml> --name <run_name>",
        "python -m autoform.eval run --repo_dir <lean_repo> --code_dir <lean_source_dir> --task_file <targets.yaml> --book_dir <book_dir>",
        "python -m autoform.visualizer.app --runs-dir <workspace> --port 8003",
    )
    return AutoformHarnessProfile(
        root=str(root),
        exists=exists,
        git_commit=_git_output(root, "rev-parse", "HEAD") if exists else "",
        remote_url=_git_output(root, "remote", "get-url", "origin") if exists else "",
        has_statement_extraction=(root / "autoform" / "statement_extraction" / "extraction.py").exists(),
        has_lean_eval=(root / "autoform" / "eval" / "lean_checks.py").exists(),
        has_dependency_graph_eval=(root / "autoform" / "eval" / "dependency_graph" / "builder.py").exists(),
        has_lean_proof_checker=(root / "tools" / "execution" / "lean" / "proof_checker.py").exists(),
        has_lean_repl_tool=(root / "tools" / "execution" / "lean" / "repl" / "core.py").exists(),
        has_native_lsp_tool=(root / "tools" / "execution" / "lean" / "native_lsp" / "session.py").exists(),
        has_lean_skill_docs=any((root / "autoform" / "bot" / "skills" / "lean").glob("*.md")) if exists else False,
        has_multi_agent_bot=(root / "autoform" / "bot" / "main.py").exists(),
        has_visualizer=(root / "autoform" / "visualizer" / "app.py").exists(),
        usage_policy="integration_reference_no_training_export",
        command_templates=command_templates,
        reusable_modules=modules,
    )


def audit_autoform_harness(out_dir: Path | None = None, root: Path = AUTOFORM_BOT_ROOT) -> dict[str, object]:
    profile = build_autoform_harness_profile(root)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "profile": asdict(profile),
        "ready_for_integration": (
            profile.exists
            and profile.has_statement_extraction
            and profile.has_lean_eval
            and profile.has_dependency_graph_eval
            and profile.has_lean_proof_checker
            and profile.has_lean_repl_tool
            and profile.has_native_lsp_tool
            and profile.has_lean_skill_docs
            and profile.has_multi_agent_bot
        ),
        "fingerprint": stable_hash(asdict(profile)),
        "limitations": [
            "adapter only records reusable harness entrypoints; it does not vendor or train on external artifacts",
            "autoform-bot execution still requires its own dependency setup and model-provider keys",
            "Atlas/autoform outputs must stay out of training exports unless license terms change",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "autoform_harness_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "autoform_harness.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _git_output(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def _markdown_report(payload: dict[str, object]) -> str:
    profile = payload.get("profile", {})
    if not isinstance(profile, dict):
        profile = {}
    commands = _string_sequence(profile.get("command_templates", []))
    modules = _string_sequence(profile.get("reusable_modules", []))
    lines = [
        "# Autoform-Bot Harness Integration",
        "",
        f"- Ready: {payload.get('ready_for_integration')}",
        f"- Root: `{profile.get('root', '')}`",
        f"- Commit: `{str(profile.get('git_commit', ''))[:12]}`",
        f"- Usage policy: `{profile.get('usage_policy', '')}`",
        f"- Fingerprint: `{payload.get('fingerprint')}`",
        "",
        "## Reusable Modules",
        "",
        *(f"- `{module}`" for module in modules),
        "",
        "## Command Templates",
        "",
        *(f"- `{command}`" for command in commands),
    ]
    return "\n".join(lines) + "\n"


def _string_sequence(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value]

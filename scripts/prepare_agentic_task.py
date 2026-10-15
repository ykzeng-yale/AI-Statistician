"""Prepare a new AI-Scientist-v3 task using the existing research guidance."""

from __future__ import annotations

import argparse
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "skills" / "statistical-research"

TASK = """# Goal

Investigate the complete brief quoted below;
[research_brief.md](resources/search/research_brief.md)
preserves the original bytes. Read the existing
[statistical research guidance](resources/search/statistical-research/SKILL.md) and its
linked Markdown references, including
[workspaces](resources/search/statistical-research/references/workspaces.md) and
[tooling](resources/search/statistical-research/references/tooling.md).

Respect task intent and permitted-source restrictions. For known-method
reconstruction, pin and disclose paper, code, data and environment versions,
reproduce relevant baselines and retain discrepancies. Source-assisted
reconstruction is not blind rediscovery or novelty. Do not use hidden judge material.

Keep durable Markdown/LaTeX theory with explicit estimands, definitions,
assumptions, justified derivations and conditions of invoked results. Use Python/R
exploratory work to challenge claims. Freeze confirmatory designs, methods,
comparators, metrics and Monte Carlo precision/stopping before outcomes; keep
exploratory and frozen confirmation results distinct, with failures and uncertainty.
Choose repetitions for the scientific question, not a universal fixed count.

Lean is optional unless task intent explicitly requires formal proof. For proof
evidence, verify exact target identity, source correspondence and an axiom-clean
check in the active pinned project. An optional Lean gap is not a universal blocker.
Seek independent review when authorized; otherwise label results unreviewed.
Deliver a coherent report linked to exact theory, code, sources and experiments,
including honest gaps, limitations and unsuccessful results.

{brief}

# Rubrics

- Assess fidelity to the brief, source policy and explicit assumptions.
- Assess the linked arguments, executed code, comparisons and empirical uncertainty.
- Distinguish proposed, executed, reproduced, reviewed and formally verified claims.
- Native evaluator/JSON scoring and self-rubrics are not mathematical proof,
  independent acceptance or scientific certification.

# Constraints

Preserve the original brief and prior task/evaluation records. Do not rerun, repair
or rescore consumed evaluations. Do not fabricate sources, results or review.
Report unavailable evidence and unresolved gaps rather than weakening the claim
silently or claiming completion from rubric scores.
"""


def prepare_task(brief: Path, destination: Path) -> Path:
    """Copy a UTF-8 brief and guidance into a strictly new task directory."""
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destination already exists: {destination}")
    original = brief.read_bytes()
    text = original.decode("utf-8")
    if not text.strip():
        raise ValueError("Research brief must not be empty")
    # Quote every line: upstream treats any unquoted heading as a section boundary.
    quoted = "> " + text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\n> ")
    paths = [SKILL / "SKILL.md", *sorted((SKILL / "references").rglob("*.md"))]
    guidance = [(path.relative_to(SKILL), path.read_bytes()) for path in paths]

    destination.mkdir(parents=True, exist_ok=False)
    public = destination / "resources" / "search"
    public.mkdir(parents=True)
    (public / "research_brief.md").write_bytes(original)
    (destination / "task.md").write_text(TASK.format(brief=quoted), encoding="utf-8")
    for relative, content in guidance:
        target = public / "statistical-research" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        prepare_task(args.brief, args.destination)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

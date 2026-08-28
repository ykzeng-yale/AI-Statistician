from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .research_schema import load_open_research_questions


UNSUPPORTED_PROBLEM_CLASS = "unsupported_frontier_question"


@dataclass(frozen=True)
class ResearchIntakeAuditRow:
    question_id: str
    source: str
    expected: str
    ok: bool
    problem_class: str
    title: str
    error: str | None = None


def audit_research_question_intake(
    out_dir: Path | None = None,
    *,
    supported_files: tuple[Path, ...] | None = None,
    unsupported_files: tuple[Path, ...] | None = None,
) -> dict[str, object]:
    """Audit paper-style research-question normalization and rejection behavior."""

    from .research_lab import ProblemFormalizer, build_research_provenance

    supported_files = supported_files or (
        Path("examples/research_questions.json"),
        Path("examples/research_paper_abstracts.md"),
    )
    unsupported_files = unsupported_files or (Path("examples/research_unsupported_paper_abstracts.md"),)

    formalizer = ProblemFormalizer()
    rows: list[ResearchIntakeAuditRow] = []
    for path in supported_files:
        for question in load_open_research_questions(path):
            try:
                problem = formalizer.formalize(question)
            except Exception as exc:
                rows.append(
                    ResearchIntakeAuditRow(
                        question_id=question.id,
                        source=str(path),
                        expected="accepted",
                        ok=False,
                        problem_class="<exception>",
                        title=question.title,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue
            ok = problem.problem_class != UNSUPPORTED_PROBLEM_CLASS
            rows.append(
                ResearchIntakeAuditRow(
                    question_id=question.id,
                    source=str(path),
                    expected="accepted",
                    ok=ok,
                    problem_class=problem.problem_class,
                    title=question.title,
                    error=None if ok else "supported research example was routed to manual review",
                )
            )

    for path in unsupported_files:
        for question in load_open_research_questions(path):
            try:
                problem = formalizer.formalize(question)
            except Exception as exc:
                rows.append(
                    ResearchIntakeAuditRow(
                        question_id=question.id,
                        source=str(path),
                        expected="rejected",
                        ok=True,
                        problem_class="<exception>",
                        title=question.title,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue
            ok = problem.problem_class == UNSUPPORTED_PROBLEM_CLASS
            rows.append(
                ResearchIntakeAuditRow(
                    question_id=question.id,
                    source=str(path),
                    expected="rejected",
                    ok=ok,
                    problem_class=problem.problem_class,
                    title=question.title,
                    error=None if ok else "unsupported frontier example was accepted by deterministic v0 formalizer",
                )
            )

    supported_rows = [row for row in rows if row.expected == "accepted"]
    unsupported_rows = [row for row in rows if row.expected == "rejected"]
    supported_classes = sorted({row.problem_class for row in supported_rows if row.ok})
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provenance": build_research_provenance(),
        "supported_files": [str(path) for path in supported_files],
        "unsupported_files": [str(path) for path in unsupported_files],
        "n_supported": len(supported_rows),
        "n_supported_accepted": sum(1 for row in supported_rows if row.ok),
        "n_unsupported": len(unsupported_rows),
        "n_unsupported_rejected": sum(1 for row in unsupported_rows if row.ok),
        "supported_problem_classes": supported_classes,
        "all_ok": all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "research_intake_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    return payload

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .research_intake_audit import UNSUPPORTED_PROBLEM_CLASS
from .research_lab import ProblemFormalizer, build_research_provenance
from .research_schema import OpenResearchQuestion


@dataclass(frozen=True)
class FrontierBenchmarkQuestion:
    id: str
    title: str
    topic: str
    source: str
    open_question: str
    assumptions: str
    expected_results: tuple[str, ...]

    def to_open_research_question(self) -> OpenResearchQuestion:
        description = "\n".join(
            part
            for part in (
                f"Open question: {self.open_question}",
                f"Assumptions to recover: {self.assumptions}",
                "Expected theoretical results: " + "; ".join(self.expected_results),
            )
            if part.strip()
        )
        tags = tuple(tag for tag in re.split(r"[_\\s-]+", self.topic.lower()) if tag)
        return OpenResearchQuestion(
            id=self.id,
            title=self.title,
            description=description,
            tags=tags,
        )


@dataclass(frozen=True)
class FrontierCoverageRow:
    question_id: str
    topic: str
    title: str
    source: str
    problem_class: str
    supported: bool
    open_question: str
    assumptions: str
    expected_results: tuple[str, ...]


def load_frontier_benchmark_questions(path: Path) -> list[FrontierBenchmarkQuestion]:
    """Parse the Markdown frontier benchmark into paper-style questions."""

    text = path.read_text(encoding="utf-8")
    topic = ""
    current: dict[str, Any] | None = None
    rows: list[FrontierBenchmarkQuestion] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        topic_match = re.match(r"^##\s+(.+?)\s*$", line)
        question_match = re.match(r"^###\s+([A-Za-z0-9_.-]+)\s*:\s*(.+?)\s*$", line)
        if topic_match and not question_match:
            if current:
                rows.append(_finish_question(current))
                current = None
            title = topic_match.group(1).strip()
            if title not in {"Scope and Sources", "Topic Index"}:
                topic = _topic_slug(title)
            continue
        if question_match:
            if current:
                rows.append(_finish_question(current))
            question_id = question_match.group(1).strip()
            current = {
                "id": question_id,
                "title": question_match.group(2).strip(),
                "topic": _topic_from_question_id(question_id) or topic,
                "source": "",
                "open_question": "",
                "assumptions": "",
                "expected_results": [],
                "_collect_expected": False,
            }
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("- Source:"):
            current["source"] = stripped.split(":", 1)[1].strip()
            current["_collect_expected"] = False
        elif stripped.startswith("- Open question:"):
            current["open_question"] = stripped.split(":", 1)[1].strip()
            current["_collect_expected"] = False
        elif stripped.startswith("- Assumptions to recover:"):
            current["assumptions"] = stripped.split(":", 1)[1].strip()
            current["_collect_expected"] = False
        elif stripped.startswith("- Expected theoretical results:"):
            current["_collect_expected"] = True
        elif current.get("_collect_expected") and stripped.startswith("- "):
            current["expected_results"].append(stripped[2:].strip())
        elif stripped and not stripped.startswith("-"):
            current["_collect_expected"] = False
    if current:
        rows.append(_finish_question(current))
    return rows


def audit_frontier_coverage(
    out_dir: Path | None = None,
    *,
    benchmark_file: Path = Path("docs/frontier_stat_theory_benchmark.md"),
) -> dict[str, object]:
    """Measure deterministic research-lab coverage over the frontier benchmark document."""

    questions = load_frontier_benchmark_questions(benchmark_file)
    formalizer = ProblemFormalizer()
    rows: list[FrontierCoverageRow] = []
    for question in questions:
        open_question = question.to_open_research_question()
        problem = formalizer.formalize(open_question)
        rows.append(
            FrontierCoverageRow(
                question_id=question.id,
                topic=question.topic,
                title=question.title,
                source=question.source,
                problem_class=problem.problem_class,
                supported=problem.problem_class != UNSUPPORTED_PROBLEM_CLASS,
                open_question=question.open_question,
                assumptions=question.assumptions,
                expected_results=question.expected_results,
            )
        )

    ids = [row.id for row in questions]
    duplicate_ids = sorted([question_id for question_id, count in Counter(ids).items() if count > 1])
    missing_required = [
        row.id
        for row in questions
        if not row.open_question or not row.assumptions or not row.expected_results
    ]
    by_problem_class = Counter(row.problem_class for row in rows)
    by_topic: dict[str, dict[str, object]] = {}
    for topic, topic_rows in _group_by_topic(rows).items():
        topic_classes = Counter(row.problem_class for row in topic_rows)
        supported = sum(1 for row in topic_rows if row.supported)
        by_topic[topic] = {
            "n_questions": len(topic_rows),
            "n_supported": supported,
            "supported_rate": supported / len(topic_rows) if topic_rows else 0.0,
            "problem_classes": dict(sorted(topic_classes.items())),
        }

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "provenance": build_research_provenance(),
        "n_questions": len(rows),
        "n_supported": sum(1 for row in rows if row.supported),
        "supported_rate": (sum(1 for row in rows if row.supported) / len(rows)) if rows else 0.0,
        "n_unsupported": sum(1 for row in rows if not row.supported),
        "by_problem_class": dict(sorted(by_problem_class.items())),
        "by_topic": by_topic,
        "duplicate_ids": duplicate_ids,
        "missing_required_fields": missing_required,
        "all_ok": bool(rows) and not duplicate_ids and not missing_required,
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "frontier_coverage_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "frontier_coverage.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _finish_question(raw: dict[str, Any]) -> FrontierBenchmarkQuestion:
    return FrontierBenchmarkQuestion(
        id=str(raw["id"]),
        title=str(raw["title"]),
        topic=str(raw.get("topic") or _topic_from_question_id(str(raw["id"]))),
        source=str(raw.get("source", "")),
        open_question=str(raw.get("open_question", "")),
        assumptions=str(raw.get("assumptions", "")),
        expected_results=tuple(str(row) for row in raw.get("expected_results", ())),
    )


def _topic_from_question_id(question_id: str) -> str:
    match = re.match(r"^(.+)_\\d+$", question_id)
    return match.group(1) if match else ""


def _topic_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug or "unknown_topic"


def _group_by_topic(rows: list[FrontierCoverageRow]) -> dict[str, list[FrontierCoverageRow]]:
    grouped: dict[str, list[FrontierCoverageRow]] = defaultdict(list)
    for row in rows:
        grouped[row.topic].append(row)
    return dict(sorted(grouped.items()))


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Frontier Statistical Theory Coverage Audit",
        "",
        f"- Benchmark file: `{payload.get('benchmark_file')}`",
        f"- Parsed questions: {payload.get('n_questions')}",
        f"- Supported by deterministic v0 formalizer: {payload.get('n_supported')}/{payload.get('n_questions')} "
        f"({float(payload.get('supported_rate', 0.0)):.1%})",
        "",
        "## Coverage By Topic",
        "",
    ]
    by_topic = payload.get("by_topic", {})
    if isinstance(by_topic, dict):
        for topic, row in by_topic.items():
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{topic}`: {row.get('n_supported')}/{row.get('n_questions')} "
                f"({float(row.get('supported_rate', 0.0)):.1%})"
            )
    lines.extend(["", "## Problem Class Counts", ""])
    by_class = payload.get("by_problem_class", {})
    if isinstance(by_class, dict):
        for problem_class, count in by_class.items():
            lines.append(f"- `{problem_class}`: {count}")
    lines.extend(["", "## Unsupported Examples", ""])
    rows = payload.get("rows", [])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict) or row.get("supported"):
                continue
            lines.append(f"- `{row.get('question_id')}` ({row.get('topic')}): {row.get('title')}")
    return "\n".join(lines) + "\n"

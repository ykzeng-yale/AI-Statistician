from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .fingerprint import stable_hash
from .research_schema import OpenResearchQuestion, PaperSourceHit, ResearchProblemSpec, TheoremGoal
from .retrieval import tokens


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTIER_BENCHMARK_PATH = PROJECT_ROOT / "benchmarks" / "frontier_stat_theory_benchmark.json"
AI_FOR_MATH_PAPER_LOG_PATH = PROJECT_ROOT / "AI for Math Resources" / "paper_links.json"


@dataclass(frozen=True)
class PaperSourceRecord:
    id: str
    title: str
    source_type: str
    source_path: str
    topic: str
    journal: str = ""
    publication_date: str = ""
    doi: str = ""
    url: str = ""
    searchable_text: str = ""
    summary: str = ""
    withheld_fields: tuple[str, ...] = ()


def build_paper_source_index(
    *,
    frontier_benchmark_path: Path = FRONTIER_BENCHMARK_PATH,
    ai_for_math_paper_log_path: Path = AI_FOR_MATH_PAPER_LOG_PATH,
) -> list[PaperSourceRecord]:
    """Build a local paper/source index for research trace grounding.

    The frontier benchmark intentionally contains gold-standard expected
    theoretical results. Those fields are not placed in ``searchable_text`` so
    the benchmark retriever cannot leak withheld targets into theory planning.
    """

    records: list[PaperSourceRecord] = []
    if frontier_benchmark_path.exists():
        records.extend(_frontier_benchmark_records(frontier_benchmark_path))
    if ai_for_math_paper_log_path.exists():
        records.extend(_ai_for_math_records(ai_for_math_paper_log_path))
    return records


def retrieve_paper_sources(
    question: OpenResearchQuestion,
    problem: ResearchProblemSpec,
    theorem_goals: list[TheoremGoal],
    *,
    records: list[PaperSourceRecord] | None = None,
    k: int = 5,
) -> list[PaperSourceHit]:
    corpus = records if records is not None else build_paper_source_index()
    query = _paper_query(question, problem, theorem_goals)
    query_tokens = tokens(query)
    hits: list[PaperSourceHit] = []
    for record in corpus:
        record_tokens = tokens(record.searchable_text)
        overlap = query_tokens & record_tokens
        if not overlap:
            continue
        source_bonus = 8.0 if record.source_type == "frontier_stat_paper" else 3.0
        class_bonus = 6.0 if problem.problem_class.replace("_", " ") in record.searchable_text.lower() else 0.0
        score = float(2 * len(overlap) + source_bonus + class_bonus)
        hits.append(
            PaperSourceHit(
                id=record.id,
                title=record.title,
                source_type=record.source_type,
                source_path=record.source_path,
                topic=record.topic,
                journal=record.journal,
                publication_date=record.publication_date,
                doi=record.doi,
                url=record.url,
                score=score,
                matched_terms=tuple(sorted(overlap))[:30],
                summary=record.summary,
                withheld_fields=record.withheld_fields,
            )
        )
    return sorted(hits, key=lambda hit: (-hit.score, hit.source_type, hit.id))[:k]


def paper_source_index_fingerprint(records: list[PaperSourceRecord] | None = None) -> str:
    corpus = records if records is not None else build_paper_source_index()
    return stable_hash([asdict(record) for record in corpus])


def _frontier_benchmark_records(path: Path) -> list[PaperSourceRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records: list[PaperSourceRecord] = []
    for topic in payload.get("topics", []):
        topic_id = str(topic.get("id", ""))
        topic_name = str(topic.get("name", topic_id))
        topic_question = str(topic.get("topic_question", ""))
        for paper in topic.get("papers", []):
            assumptions = " ".join(str(item) for item in paper.get("assumptions_to_recover", []))
            searchable = " ".join(
                [
                    str(paper.get("title", "")),
                    topic_name,
                    topic_question,
                    str(paper.get("open_question", "")),
                    assumptions,
                    str(paper.get("journal", "")),
                ]
            )
            summary = "; ".join(
                part
                for part in (
                    str(paper.get("open_question", "")),
                    f"Assumptions: {assumptions}" if assumptions else "",
                )
                if part
            )
            records.append(
                PaperSourceRecord(
                    id=str(paper.get("id", "")),
                    title=str(paper.get("title", "")),
                    source_type="frontier_stat_paper",
                    source_path=str(path),
                    topic=topic_name,
                    journal=str(paper.get("journal", "")),
                    publication_date=str(paper.get("publication_date", "")),
                    doi=str(paper.get("doi", "")),
                    url=str(paper.get("url", "")),
                    searchable_text=searchable,
                    summary=summary,
                    withheld_fields=("expected_theoretical_results", "evaluation_prompt"),
                )
            )
    return records


def _ai_for_math_records(path: Path) -> list[PaperSourceRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records: list[PaperSourceRecord] = []
    for group_name, papers in payload.get("groups", {}).items():
        if not isinstance(papers, list):
            continue
        for idx, paper in enumerate(papers):
            if not isinstance(paper, dict):
                continue
            title = str(paper.get("title", ""))
            tags = tuple(str(tag) for tag in paper.get("tags", []) if tag)
            searchable = " ".join(
                [
                    title,
                    str(group_name),
                    str(paper.get("registry_category", "")),
                    " ".join(tags),
                    str(paper.get("source", "")),
                ]
            )
            records.append(
                PaperSourceRecord(
                    id=f"ai_math_{stable_hash([group_name, title, paper.get('url', ''), idx])[:12]}",
                    title=title,
                    source_type="ai_math_paper",
                    source_path=str(path),
                    topic=str(group_name),
                    url=str(paper.get("url", "")),
                    searchable_text=searchable,
                    summary=", ".join(tags),
                )
            )
    return records


def _paper_query(
    question: OpenResearchQuestion,
    problem: ResearchProblemSpec,
    theorem_goals: list[TheoremGoal],
) -> str:
    return " ".join(
        [
            question.title,
            question.description,
            " ".join(question.tags),
            problem.problem_class,
            problem.dgp,
            problem.estimand,
            " ".join(problem.assumptions),
            problem.asymptotic_regime,
            " ".join(problem.diagnostics),
            " ".join(goal.title + " " + goal.informal_statement for goal in theorem_goals),
        ]
    )

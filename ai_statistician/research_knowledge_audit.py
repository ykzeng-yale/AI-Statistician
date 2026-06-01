from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .research_knowledge import (
    FORMAL_INFRASTRUCTURE_KNOWLEDGE,
    KNOWLEDGE_CARDS,
    PRIMARY_KNOWLEDGE_BY_PROBLEM_CLASS,
    PROJECT_ROOT,
    retrieve_problem_knowledge,
)
from .research_lab import ProblemFormalizer, TheoryPlanner, load_open_research_questions
from .research_source_inventory import build_research_source_inventory


@dataclass(frozen=True)
class KnowledgeSourceAuditRow:
    card_id: str
    source_type: str
    location: str
    ok: bool
    reason: str = ""


@dataclass(frozen=True)
class ProblemKnowledgeAuditRow:
    question_id: str
    problem_class: str
    expected_primary: str | None
    top_hit: str | None
    has_primary: bool
    has_method_card: bool
    has_formal_infra: bool
    has_local_formal_source: bool
    has_search_infra: bool
    hits: tuple[str, ...]
    ok: bool


LOCAL_FORMAL_SOURCE_KNOWLEDGE = {
    "local_mathlib_probability",
    "local_statinference_repo",
    "empirical_process_lean",
    "lean_stat_learning_theory",
    "formal_slt",
    "lean_rademacher",
    "lean_machine_learning_lml",
    "brownian_motion_lean",
    "kolmogorov_extension_lean",
    "scilean_calculus",
    "legacy_ai_statistician_statinference",
}

FORMAL_SEARCH_KNOWLEDGE = {
    "lean_finder",
    "leandojo_reprover",
    "loogle",
    "leansearch_client_local",
    "leandojo_v2_local",
    "openprover_pipeline",
}


def audit_research_knowledge(
    out_dir: Path | None = None,
    *,
    question_file: Path = Path("examples/research_questions.json"),
) -> dict[str, object]:
    """Audit that research traces are backed by live knowledge sources.

    This is not a semantic RAG benchmark. It is a release gate for the current
    deterministic knowledge layer: cards must point at existing local files/repos
    or valid URLs, and each supported example question must retrieve both the
    primary statistical method card and at least one Lean/search infrastructure
    card.
    """

    if not question_file.is_absolute() and not question_file.exists():
        question_file = PROJECT_ROOT / question_file

    source_rows = [_audit_source(card.id, card.source_type, card.location) for card in KNOWLEDGE_CARDS]
    inventory_out = out_dir / "source_inventory" if out_dir is not None else None
    source_inventory = build_research_source_inventory(inventory_out)
    duplicate_ids = sorted(
        card_id
        for card_id in {card.id for card in KNOWLEDGE_CARDS}
        if sum(1 for card in KNOWLEDGE_CARDS if card.id == card_id) > 1
    )

    formalizer = ProblemFormalizer()
    planner = TheoryPlanner()
    problem_rows: list[ProblemKnowledgeAuditRow] = []
    for question in load_open_research_questions(question_file):
        problem = formalizer.formalize(question)
        _procedures, goals = planner.plan(problem)
        hits = retrieve_problem_knowledge(question, problem, goals, k=8)
        hit_ids = tuple(card.id for card in hits)
        expected_primary = PRIMARY_KNOWLEDGE_BY_PROBLEM_CLASS.get(problem.problem_class)
        has_primary = expected_primary in hit_ids if expected_primary else False
        has_method_card = any(card.source_type == "statistical_method" for card in hits)
        has_formal_infra = any(card.id in FORMAL_INFRASTRUCTURE_KNOWLEDGE for card in hits)
        has_local_formal_source = any(card.id in LOCAL_FORMAL_SOURCE_KNOWLEDGE for card in hits)
        has_search_infra = any(card.id in FORMAL_SEARCH_KNOWLEDGE for card in hits)
        ok = (
            bool(hit_ids)
            and (expected_primary is None or has_primary)
            and has_method_card
            and has_formal_infra
            and has_local_formal_source
            and has_search_infra
        )
        problem_rows.append(
            ProblemKnowledgeAuditRow(
                question_id=question.id,
                problem_class=problem.problem_class,
                expected_primary=expected_primary,
                top_hit=hit_ids[0] if hit_ids else None,
                has_primary=has_primary,
                has_method_card=has_method_card,
                has_formal_infra=has_formal_infra,
                has_local_formal_source=has_local_formal_source,
                has_search_infra=has_search_infra,
                hits=hit_ids,
                ok=ok,
            )
        )

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_file": str(question_file),
        "n_cards": len(KNOWLEDGE_CARDS),
        "n_source_ok": sum(1 for row in source_rows if row.ok),
        "source_inventory": {
            "n_sources": source_inventory["n_sources"],
            "n_ok": source_inventory["n_ok"],
            "all_ok": source_inventory["all_ok"],
            "inventory_fingerprint": source_inventory["inventory_fingerprint"],
        },
        "n_problem_rows": len(problem_rows),
        "n_problem_ok": sum(1 for row in problem_rows if row.ok),
        "duplicate_ids": duplicate_ids,
        "all_ok": (
            not duplicate_ids
            and all(row.ok for row in source_rows)
            and bool(source_inventory["all_ok"])
            and all(row.ok for row in problem_rows)
        ),
        "source_rows": [asdict(row) for row in source_rows],
        "problem_rows": [asdict(row) for row in problem_rows],
    }
    if out_dir is not None:
        payload["source_inventory_artifacts"] = {
            "manifest": str(inventory_out / "research_source_inventory_manifest.json"),
            "report": str(inventory_out / "research_source_inventory.md"),
        }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "research_knowledge_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "research_knowledge_audit.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _audit_source(card_id: str, source_type: str, location: str) -> KnowledgeSourceAuditRow:
    if location == "internal-method-card":
        return KnowledgeSourceAuditRow(card_id, source_type, location, True)
    parsed = urlparse(location)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return KnowledgeSourceAuditRow(card_id, source_type, location, True)

    path = Path(location).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.exists():
        return KnowledgeSourceAuditRow(card_id, source_type, location, True)
    return KnowledgeSourceAuditRow(card_id, source_type, location, False, f"missing path: {path}")


def _markdown_report(payload: dict[str, object]) -> str:
    source_rows = list(payload["source_rows"])  # type: ignore[index]
    problem_rows = list(payload["problem_rows"])  # type: ignore[index]
    lines = [
        "# Research Knowledge Audit",
        "",
        f"- Cards: {payload['n_source_ok']}/{payload['n_cards']} source locations valid",
        f"- Source inventory: {payload['source_inventory']['n_ok']}/{payload['source_inventory']['n_sources']} clean",
        f"- Problem retrieval rows: {payload['n_problem_ok']}/{payload['n_problem_rows']} ok",
        f"- All ok: `{payload['all_ok']}`",
        "",
        "## Problem Retrieval",
        "",
        "| Question | Class | Expected primary | Top hit | Method | Local formal | Search | OK |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in problem_rows:
        lines.append(
            "| {question_id} | {problem_class} | {expected_primary} | {top_hit} | {has_method_card} | {has_local_formal_source} | {has_search_infra} | {ok} |".format(
                **row
            )
        )
    lines.extend(["", "## Source Locations", "", "| Card | Type | OK | Location / reason |", "|---|---|---:|---|"])
    for row in source_rows:
        detail = row["reason"] or row["location"]
        lines.append(f"| {row['card_id']} | {row['source_type']} | {row['ok']} | `{detail}` |")
    return "\n".join(lines) + "\n"

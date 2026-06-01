from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .research_lab import ProblemFormalizer
from .research_schema import OpenResearchQuestion


ADVERSARIAL_INTAKE_AUDIT_SCHEMA_VERSION = 1
UNSUPPORTED_PROBLEM_CLASS = "unsupported_frontier_question"


@dataclass(frozen=True)
class AdversarialIntakeCase:
    id: str
    title: str
    description: str
    tags: tuple[str, ...]
    expected_behavior: str
    risk: str


@dataclass(frozen=True)
class AdversarialIntakeRow:
    case_id: str
    risk: str
    expected_behavior: str
    observed_behavior: str
    routed_problem_class: str
    ok: bool
    issue: str


def audit_adversarial_unsupported_intake(
    out_dir: Path | None = None,
    *,
    benchmark_file: Path = Path("benchmarks/adversarial_unsupported_intake.json"),
) -> dict[str, object]:
    """Audit unsupported/adversarial intake guardrails.

    This is an honesty-boundary benchmark. Passing means the deterministic
    intake layer refuses or scopes prompts that are vague, contradictory,
    unsupported, gold-answer-leaking, or prompt-injection-like. It does not
    measure theorem proving or simulation quality.
    """

    cases = load_adversarial_intake_cases(benchmark_file)
    formalizer = ProblemFormalizer()
    rows = [_run_case(case, formalizer) for case in cases]
    rejected = [row for row in rows if row.observed_behavior == "rejected"]
    by_risk: dict[str, int] = {}
    for row in rows:
        by_risk[row.risk] = by_risk.get(row.risk, 0) + 1
    payload: dict[str, object] = {
        "schema_version": ADVERSARIAL_INTAKE_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_file),
        "n_cases": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_rejected": len(rejected),
        "n_accepted": len(rows) - len(rejected),
        "by_risk": by_risk,
        "all_ok": bool(rows) and all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
        "limitations": [
            "adversarial intake checks routing and overclaim refusal, not theorem proving",
            "rejecting a prompt means manual review is required, not that the underlying topic is mathematically unimportant",
            "prompt-leakage rejection protects benchmark integrity; it is not a proof of leakage-free LLM behavior",
        ],
        "audit_fingerprint": stable_hash([asdict(row) for row in rows]),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "adversarial_intake_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "adversarial_intake.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def load_adversarial_intake_cases(path: Path) -> tuple[AdversarialIntakeCase, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("cases", payload)
    return tuple(
        AdversarialIntakeCase(
            id=str(row["id"]),
            title=str(row.get("title", row["id"])),
            description=str(row["description"]),
            tags=tuple(str(tag) for tag in row.get("tags", ())),
            expected_behavior=str(row.get("expected_behavior", "reject")),
            risk=str(row.get("risk", "unspecified")),
        )
        for row in rows
    )


def _run_case(case: AdversarialIntakeCase, formalizer: ProblemFormalizer) -> AdversarialIntakeRow:
    question = OpenResearchQuestion(
        id=case.id,
        title=case.title,
        description=case.description,
        tags=case.tags,
    )
    problem = formalizer.formalize(question)
    observed = "rejected" if problem.problem_class == UNSUPPORTED_PROBLEM_CLASS else "accepted"
    expected = _normalize_expected_behavior(case.expected_behavior)
    ok = observed == expected
    issue = "" if ok else f"expected {expected}, observed {observed}"
    return AdversarialIntakeRow(
        case_id=case.id,
        risk=case.risk,
        expected_behavior=expected,
        observed_behavior=observed,
        routed_problem_class=problem.problem_class,
        ok=ok,
        issue=issue,
    )


def _normalize_expected_behavior(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"reject", "rejected", "manual_review", "manual-review"}:
        return "rejected"
    if normalized in {"accept", "accepted"}:
        return "accepted"
    return normalized


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Adversarial Unsupported Intake Audit",
        "",
        f"- Cases: {payload.get('n_cases')}",
        f"- OK: {payload.get('n_ok')}",
        f"- Rejected/manual-review routed: {payload.get('n_rejected')}",
        f"- Accepted: {payload.get('n_accepted')}",
        f"- All OK: `{payload.get('all_ok')}`",
        "",
        "## Rows",
        "",
        "| Case | Risk | Expected | Observed | Routed class | OK | Issue |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| `{row.get('case_id')}` | `{row.get('risk')}` | `{row.get('expected_behavior')}` | "
            f"`{row.get('observed_behavior')}` | `{row.get('routed_problem_class')}` | "
            f"`{row.get('ok')}` | {row.get('issue', '')} |"
        )
    lines.extend(["", "## Honesty Boundary", ""])
    for limitation in payload.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)

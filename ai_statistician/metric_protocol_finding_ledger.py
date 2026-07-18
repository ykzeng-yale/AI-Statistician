from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from .fingerprint import stable_hash


METRIC_PROTOCOL_FINDING_UNRESOLVED = "UNRESOLVED"
METRIC_PROTOCOL_FINDING_RESOLVED = "RESOLVED"
METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY = (
    "RESOLVED_BY_CURRENT_THEORY"
)
METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT = (
    "RETRACTED_RUNTIME_CONTRACT_CONFLICT"
)
METRIC_PROTOCOL_FINDING_ADVISORY = "ADVISORY"
METRIC_PROTOCOL_PRIOR_FINDING_REVIEW_STATUSES = (
    METRIC_PROTOCOL_FINDING_UNRESOLVED,
    METRIC_PROTOCOL_FINDING_RESOLVED,
    METRIC_PROTOCOL_FINDING_RESOLVED_BY_CURRENT_THEORY,
    METRIC_PROTOCOL_FINDING_RETRACTED_RUNTIME_CONTRACT_CONFLICT,
)


def metric_protocol_finding_id(
    *,
    question_id: str,
    finding: Mapping[str, Any],
    preserve_existing: bool = True,
) -> str:
    existing = str(finding.get("finding_id", "") or "").strip()
    if preserve_existing and existing:
        return existing
    identity = {
        "question_id": str(question_id),
        "category": str(finding.get("category", "") or "").strip(),
        "summary": str(finding.get("summary", "") or "").strip(),
        "required_change": str(
            finding.get("required_change", "") or ""
        ).strip(),
        "evidence_refs": [
            str(value).strip()
            for value in finding.get("evidence_refs", []) or []
            if str(value).strip()
        ],
    }
    return "metric_protocol_finding:" + stable_hash(identity)[:20]


def normalize_metric_protocol_findings(
    *,
    question_id: str,
    findings: Any,
    preserve_existing_ids: bool = True,
) -> list[dict[str, Any]]:
    rows = (
        [dict(row) for row in findings if isinstance(row, Mapping)]
        if isinstance(findings, list)
        else []
    )
    for row in rows:
        row["finding_id"] = metric_protocol_finding_id(
            question_id=question_id,
            finding=row,
            preserve_existing=preserve_existing_ids,
        )
    return rows


def update_metric_protocol_finding_ledger(
    *,
    question_id: str,
    prior_ledger: Sequence[Mapping[str, Any]],
    prior_finding_reviews: Any,
    current_findings: Any,
    current_verdict: str,
    review_packet_id: str,
    revision_index: int,
) -> list[dict[str, Any]]:
    ordered_ids: list[str] = []
    ledger_by_id: dict[str, dict[str, Any]] = {}
    for raw_row in prior_ledger:
        if not isinstance(raw_row, Mapping):
            continue
        row = deepcopy(dict(raw_row))
        finding = row.get("finding", {})
        if not isinstance(finding, Mapping):
            finding = {}
        finding_id = str(row.get("finding_id", "") or "").strip()
        if not finding_id and finding:
            finding_id = metric_protocol_finding_id(
                question_id=question_id,
                finding=finding,
            )
        if not finding_id:
            continue
        row["finding_id"] = finding_id
        row["finding"] = deepcopy(dict(finding))
        ordered_ids.append(finding_id)
        ledger_by_id[finding_id] = row

    review_rows = (
        [dict(row) for row in prior_finding_reviews if isinstance(row, Mapping)]
        if isinstance(prior_finding_reviews, list)
        else []
    )
    for review in review_rows:
        finding_id = str(review.get("finding_id", "") or "").strip()
        if finding_id not in ledger_by_id:
            continue
        status = str(review.get("status", "") or "").strip().upper()
        if status not in METRIC_PROTOCOL_PRIOR_FINDING_REVIEW_STATUSES:
            continue
        row = ledger_by_id[finding_id]
        row["status"] = status
        row["resolution"] = {
            "status": status,
            "rationale": str(review.get("rationale", "") or "").strip(),
            "evidence_refs": [
                str(value).strip()
                for value in review.get("evidence_refs", []) or []
                if str(value).strip()
            ],
            "review_packet_id": str(review_packet_id),
            "revision_index": int(revision_index),
        }

    verdict = str(current_verdict or "").strip().upper()
    current_status = (
        METRIC_PROTOCOL_FINDING_ADVISORY
        if verdict == "ACCEPT"
        else METRIC_PROTOCOL_FINDING_UNRESOLVED
    )
    for finding in normalize_metric_protocol_findings(
        question_id=question_id,
        findings=current_findings,
    ):
        finding_id = str(finding["finding_id"])
        existing = ledger_by_id.get(finding_id, {})
        source_review_packet_ids = [
            str(value)
            for value in existing.get("source_review_packet_ids", []) or []
            if str(value).strip()
        ]
        if review_packet_id:
            source_review_packet_ids.append(str(review_packet_id))
        first_seen_revision_index = existing.get(
            "first_seen_revision_index", revision_index
        )
        try:
            first_seen_revision_index = int(first_seen_revision_index)
        except (TypeError, ValueError):
            first_seen_revision_index = int(revision_index)
        row = {
            **deepcopy(dict(existing)),
            "finding_id": finding_id,
            "status": current_status,
            "first_seen_revision_index": first_seen_revision_index,
            "latest_seen_revision_index": int(revision_index),
            "source_review_packet_ids": list(
                dict.fromkeys(source_review_packet_ids)
            ),
            "finding": finding,
        }
        if current_status == METRIC_PROTOCOL_FINDING_UNRESOLVED:
            row.pop("resolution", None)
        if finding_id not in ledger_by_id:
            ordered_ids.append(finding_id)
        ledger_by_id[finding_id] = row

    return [ledger_by_id[finding_id] for finding_id in ordered_ids]


def active_metric_protocol_finding_ledger(
    ledger: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        deepcopy(dict(row))
        for row in ledger
        if isinstance(row, Mapping)
        and str(row.get("status", "") or "").strip().upper()
        == METRIC_PROTOCOL_FINDING_UNRESOLVED
    ]


def metric_protocol_finding_ledger_from_review_history(
    *,
    question_id: str,
    semantic_review_history: Any,
) -> list[dict[str, Any]]:
    history = (
        [dict(row) for row in semantic_review_history if isinstance(row, Mapping)]
        if isinstance(semantic_review_history, list)
        else []
    )
    for review in reversed(history):
        ledger = review.get("cumulative_finding_ledger", [])
        if isinstance(ledger, list) and ledger:
            return [
                deepcopy(dict(row))
                for row in ledger
                if isinstance(row, Mapping)
            ]
    if not history:
        return []
    final_review = history[-1]
    return update_metric_protocol_finding_ledger(
        question_id=question_id,
        prior_ledger=[],
        prior_finding_reviews=[],
        current_findings=final_review.get("findings", []),
        current_verdict=str(final_review.get("overall_verdict", "") or ""),
        review_packet_id=str(
            final_review.get("semantic_review_packet_id", "") or ""
        ),
        revision_index=int(final_review.get("revision_index", 0) or 0),
    )


def metric_protocol_finding_ledger_fingerprint(
    ledger: Sequence[Mapping[str, Any]],
) -> str:
    return stable_hash([dict(row) for row in ledger if isinstance(row, Mapping)])

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .questions import (
    estimator_registry_fingerprint,
    load_question_file,
    question_from_json,
    question_registry_fingerprint,
)


@dataclass(frozen=True)
class IntakeAuditRow:
    question_id: str
    source: str
    expected: str
    ok: bool
    dgp_family: str | None = None
    estimator_family: str | None = None
    error: str | None = None


def audit_question_intake(
    out_dir: Path | None = None,
    *,
    supported_files: tuple[Path, ...] | None = None,
    unsupported_files: tuple[Path, ...] | None = None,
) -> dict[str, object]:
    """Audit question intake acceptance and rejection behavior."""

    supported_files = supported_files or (
        Path("examples/questions.json"),
        Path("examples/partial_questions.json"),
    )
    unsupported_files = unsupported_files or (Path("examples/unsupported_questions.json"),)

    rows: list[IntakeAuditRow] = []
    for path in supported_files:
        for question in load_question_file(path):
            rows.append(
                IntakeAuditRow(
                    question_id=question.id,
                    source=str(path),
                    expected="accepted",
                    ok=True,
                    dgp_family=question.dgp_family,
                    estimator_family=question.estimator_family,
                )
            )

    for path in unsupported_files:
        for raw in _load_raw_questions(path):
            question_id = str(raw.get("id", "<missing id>"))
            try:
                question = question_from_json(raw)
            except Exception as exc:
                rows.append(
                    IntakeAuditRow(
                        question_id=question_id,
                        source=str(path),
                        expected="rejected",
                        ok=True,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
            else:
                rows.append(
                    IntakeAuditRow(
                        question_id=question.id,
                        source=str(path),
                        expected="rejected",
                        ok=False,
                        dgp_family=question.dgp_family,
                        estimator_family=question.estimator_family,
                        error="unsupported example was accepted",
                    )
                )

    supported_rows = [row for row in rows if row.expected == "accepted"]
    unsupported_rows = [row for row in rows if row.expected == "rejected"]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_registry_fingerprint": question_registry_fingerprint(),
        "estimator_registry_fingerprint": estimator_registry_fingerprint(),
        "supported_files": [str(path) for path in supported_files],
        "unsupported_files": [str(path) for path in unsupported_files],
        "n_supported": len(supported_rows),
        "n_supported_accepted": sum(1 for row in supported_rows if row.ok),
        "n_unsupported": len(unsupported_rows),
        "n_unsupported_rejected": sum(1 for row in unsupported_rows if row.ok),
        "all_ok": all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "intake_audit_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
    return payload


def _load_raw_questions(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [dict(row) for row in data]
    if isinstance(data, dict) and isinstance(data.get("questions"), list):
        return [dict(row) for row in data["questions"]]
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"unsupported question JSON shape in {path}")

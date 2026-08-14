from __future__ import annotations

import json

from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    GeneratorResponse,
)
from ai_statistician.theory_semantic_gold_judge import (
    run_theory_semantic_gold_judge,
    validate_theory_semantic_gold_judgment,
)


CLAIM_IDS = ["claim:definition", "claim:limit"]
CASE_IDS = ["case:a", "case:b"]


def _claim_rows(*, violated: str = "") -> list[dict[str, object]]:
    return [
        {
            "claim_id": claim_id,
            "status": "VIOLATED" if claim_id == violated else "SATISFIED",
        }
        for claim_id in CLAIM_IDS
    ]


def _assessment(case_id: str, *, violated: str = "") -> dict[str, object]:
    return {
        "case_id": case_id,
        "status": "FAIL" if violated else "PASS",
        "claim_assessments": _claim_rows(violated=violated),
    }


def _packet(*, misclassify_second_case: bool = False) -> dict[str, object]:
    return {
        "assessments": [
            _assessment("case:a"),
            _assessment(
                "case:b",
                violated="" if misclassify_second_case else "claim:limit",
            ),
            _assessment("candidate"),
        ],
    }


class _RecordingProvider:
    provider_name = "static"

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = packet
        self.request = None

    def generate(self, request):
        self.request = request
        return GeneratorResponse(
            text=json.dumps(self.packet),
            provider=self.provider_name,
            model=request.model,
        )


def _run(
    provider: _RecordingProvider,
    *,
    semantic_artifact_role: str = "theory",
) -> dict[str, object]:
    return run_theory_semantic_gold_judge(
        provider=provider,
        task_id="known-result",
        visible_question={"id": "known-result", "description": "derive it"},
        candidate_documents=[
            {"path": "candidate.md", "sha256": "candidate", "content": "candidate"}
        ],
        reference_documents=[
            {"path": "reference.md", "sha256": "reference", "content": "reference"}
        ],
        rubric={
            "rubric_id": "rubric:1",
            "claims": [
                {"claim_id": "claim:definition", "criterion": "Definition is correct."},
                {"claim_id": "claim:limit", "criterion": "Limit is correct."},
            ],
        },
        calibration_cases=[
            {
                "case_id": "case:a",
                "expected_status": "PASS",
                "documents": [{"path": "a.md", "content": "correct"}],
            },
            {
                "case_id": "case:b",
                "expected_status": "FAIL",
                "documents": [{"path": "b.md", "content": "wrong limit"}],
            },
        ],
        semantic_artifact_role=semantic_artifact_role,
    )


def test_semantic_gold_judge_requires_hidden_case_calibration() -> None:
    provider = _RecordingProvider(_packet())

    result = _run(provider)

    assert result["semantic_judge_calibrated"] is True
    assert result["candidate_status"] == "PASS"
    assert result["passed"] is True
    assert result["n_calibration_cases_correct"] == 2
    assert provider.request.model == LIVE_EVALUATION_CLAUDE_MODEL
    assert provider.request.metadata["model_tier"] == "haiku"
    assert "expected_status" not in provider.request.user_prompt


def test_candidate_pass_cannot_override_failed_calibration() -> None:
    result = _run(_RecordingProvider(_packet(misclassify_second_case=True)))

    assert result["semantic_judge_calibrated"] is False
    assert result["candidate_status"] == "PASS"
    assert result["passed"] is False
    assert result["n_calibration_cases_correct"] == 1


def test_theory_role_preserves_existing_judgment_contract() -> None:
    provider = _RecordingProvider(_packet())

    result = _run(provider)

    assert result["artifact_kind"] == "HiddenTheorySemanticGoldJudgment"
    assert provider.request.metadata["subsystem"] == "TheorySemanticGoldJudge"


def test_semantic_judge_records_scientific_document_role() -> None:
    provider = _RecordingProvider(_packet())

    result = _run(
        provider,
        semantic_artifact_role="source_replication_report",
    )

    assert result["artifact_kind"] == (
        "HiddenScientificDocumentSemanticGoldJudgment"
    )
    assert result["semantic_artifact_role"] == "source_replication_report"
    assert provider.request.metadata["semantic_artifact_role"] == (
        "source_replication_report"
    )


def test_semantic_judge_validator_rejects_inconsistent_overall_status() -> None:
    packet = _packet()
    candidate = packet["assessments"][-1]
    candidate["status"] = "PASS"
    candidate["claim_assessments"][0]["status"] = "VIOLATED"

    errors = validate_theory_semantic_gold_judgment(
        packet,
        claim_ids=CLAIM_IDS,
        calibration_case_ids=CASE_IDS,
    )

    assert "assessments[2] status is inconsistent with claim assessments" in errors


def test_semantic_judge_identity_checks_do_not_require_row_order() -> None:
    packet = _packet()
    packet["assessments"].reverse()
    for assessment in packet["assessments"]:
        assessment["claim_assessments"].reverse()

    assert validate_theory_semantic_gold_judgment(
        packet,
        claim_ids=CLAIM_IDS,
        calibration_case_ids=CASE_IDS,
    ) == []

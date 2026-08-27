from __future__ import annotations

import json

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    GeneratorResponse,
)
from ai_statistician.theory_semantic_gold_judge import (
    run_theory_semantic_gold_judge,
    validate_theory_semantic_gold_judgment,
)


CLAIM_IDS = ["claim:definition", "claim:limit"]
CASE_IDS = ["reference_complete", "wrong_limit"]
MODEL_CASE_IDS = ["case_0001", "case_0002"]


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
        "document_status": "PASS",
        "document_decisive_excerpt": "candidate",
        "claim_assessments": _claim_rows(violated=violated),
    }


def _packet(*, misclassify_second_case: bool = False) -> dict[str, object]:
    return {
        "assessments": [
            _assessment(CASE_IDS[0]),
            _assessment(
                CASE_IDS[1],
                violated="" if misclassify_second_case else "claim:limit",
            ),
            _assessment("candidate"),
        ],
    }


def _calibration_packet(
    *, misclassify_second_case: bool = False
) -> dict[str, object]:
    statuses = [
        (CASE_IDS[0], "PASS"),
        (
            CASE_IDS[1],
            "PASS" if misclassify_second_case else "FAIL",
        ),
    ]
    return {
        "assessments": [
            {
                "case_id": case_id,
                "status": status,
                "claim_assessments": [],
            }
            for case_id, status in statuses
        ]
    }


def _keyed_calibration_packet(
    *, misclassify_second_case: bool = False
) -> dict[str, object]:
    return {
        "assessments": {
            MODEL_CASE_IDS[0]: {"status": "PASS"},
            MODEL_CASE_IDS[1]: {
                "status": "PASS" if misclassify_second_case else "FAIL"
            },
        }
    }


def _keyed_candidate_packet(
    *,
    violated: str = "",
    document_status: str = "PASS",
    claim_ids: list[str] | None = None,
) -> dict[str, object]:
    required_claim_ids = claim_ids if claim_ids is not None else CLAIM_IDS
    return {
        "assessments": {
            "candidate": {
                "document_status": document_status,
                "document_decisive_evidence_ref": "candidate:0:0",
                "claim_statuses": {
                    claim_id: "VIOLATED" if claim_id == violated else "SATISFIED"
                    for claim_id in required_claim_ids
                },
                "decisive_evidence_refs": {
                    claim_id: "candidate:0:0"
                    for claim_id in required_claim_ids
                },
            }
        }
    }


class _RecordingProvider:
    provider_name = "static"

    def __init__(self, packets: list[dict[str, object]]) -> None:
        self.packets = packets
        self.requests = []

    def generate(self, request):
        packet = self.packets[len(self.requests)]
        self.requests.append(request)
        return GeneratorResponse(
            text=json.dumps(packet),
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
                "case_id": CASE_IDS[0],
                "expected_status": "PASS",
                "documents": [{"path": "reference_complete.md", "content": "correct"}],
            },
            {
                "case_id": CASE_IDS[1],
                "expected_status": "FAIL",
                "documents": [{"path": "wrong_limit.md", "content": "wrong limit"}],
            },
        ],
        semantic_artifact_role=semantic_artifact_role,
    )


def test_semantic_gold_judge_requires_hidden_case_calibration() -> None:
    provider = _RecordingProvider(
        [_keyed_calibration_packet(), _keyed_candidate_packet()]
    )

    result = _run(provider)

    assert result["protocol_version"] == 3
    assert result["semantic_judge_calibrated"] is True
    assert result["candidate_status"] == "PASS"
    assert result["candidate_claim_assessments"] == [
        {
            "claim_id_hash": stable_hash(claim_id),
            "status": "SATISFIED",
            "decisive_excerpt_hash": stable_hash("candidate"),
        }
        for claim_id in CLAIM_IDS
    ]
    assert result["passed"] is True
    assert result["n_calibration_cases_correct"] == 2
    assert result["n_model_calls"] == 2
    assert result["candidate_claim_model_calls"] == 1
    assert result["candidate_integrated_model_calls"] == 1
    assert result["candidate_claim_scope_isolated"] is False
    assert result["candidate_integrated_context"] is True
    assert result["candidate_document_status_requested"] is True
    assert result["candidate_document_status"] == "PASS"
    assert result["candidate_document_decisive_excerpt_hash"] == stable_hash(
        "candidate"
    )
    assert result["calibration_candidate_context_isolated"] is True
    assert result["calibration_case_ids_opaque"] is True
    assert len(provider.requests) == 2
    assert all(
        request.model == LIVE_EVALUATION_CLAUDE_MODEL
        for request in provider.requests
    )
    assert all(
        request.metadata["model_tier"] == "haiku"
        for request in provider.requests
    )
    assert "expected_status" not in provider.requests[0].user_prompt
    assert all(case_id not in provider.requests[0].user_prompt for case_id in CASE_IDS)
    assert "reference_complete.md" not in provider.requests[0].user_prompt
    assert "wrong_limit.md" not in provider.requests[0].user_prompt
    assert '"case_id": "candidate"' not in provider.requests[0].user_prompt
    assert all(case_id not in provider.requests[1].user_prompt for case_id in CASE_IDS)
    assert '"required_claim_ids": []' in provider.requests[0].user_prompt
    assert '"required_claim_ids": []' not in provider.requests[1].user_prompt
    assert '"claim:limit"' in provider.requests[1].user_prompt
    assert '"claim:definition"' in provider.requests[1].user_prompt
    assert result["calibration_claim_assessments_requested"] is False
    assert result["candidate_claim_assessments_requested"] is True
    calibration_assessments = provider.requests[0].schema["properties"][
        "assessments"
    ]
    assert calibration_assessments["type"] == "object"
    assert calibration_assessments["required"] == MODEL_CASE_IDS
    assert all(case_id not in json.dumps(provider.requests[0].schema) for case_id in CASE_IDS)
    assert all(
        row["required"] == ["status"]
        for row in calibration_assessments["properties"].values()
    )
    candidate_assessments = provider.requests[1].schema["properties"]["assessments"]
    assert candidate_assessments["required"] == ["candidate"]
    candidate_schema = candidate_assessments["properties"]["candidate"]
    assert candidate_schema["required"] == [
        "document_status",
        "document_decisive_evidence_ref",
        "claim_statuses",
        "decisive_evidence_refs",
    ]
    assert "status" not in candidate_schema["properties"]
    assert candidate_schema["properties"]["claim_statuses"]["required"] == (
        CLAIM_IDS
    )
    assert provider.requests[0].metadata["semantic_adjudication_phase"] == (
        "calibration"
    )
    assert provider.requests[1].metadata["semantic_adjudication_phase"] == (
        "candidate_integrated"
    )


def test_candidate_pass_cannot_override_failed_calibration() -> None:
    result = _run(
        _RecordingProvider(
            [
                _keyed_calibration_packet(misclassify_second_case=True),
                _keyed_candidate_packet(),
            ]
        )
    )

    assert result["semantic_judge_calibrated"] is False
    assert result["candidate_status"] == "PASS"
    assert result["passed"] is False
    assert result["n_calibration_cases_correct"] == 1


def test_theory_role_preserves_existing_judgment_contract() -> None:
    provider = _RecordingProvider(
        [_keyed_calibration_packet(), _keyed_candidate_packet()]
    )

    result = _run(provider)

    assert result["artifact_kind"] == "HiddenTheorySemanticGoldJudgment"
    assert all(
        request.metadata["subsystem"] == "TheorySemanticGoldJudge"
        for request in provider.requests
    )


def test_semantic_judge_records_scientific_document_role() -> None:
    provider = _RecordingProvider(
        [_keyed_calibration_packet(), _keyed_candidate_packet()]
    )

    result = _run(
        provider,
        semantic_artifact_role="source_replication_report",
    )

    assert result["artifact_kind"] == (
        "HiddenScientificDocumentSemanticGoldJudgment"
    )
    assert result["semantic_artifact_role"] == "source_replication_report"
    assert all(
        request.metadata["semantic_artifact_role"]
        == "source_replication_report"
        for request in provider.requests
    )


def test_candidate_status_combines_document_and_keyed_claim_statuses() -> None:
    result = _run(
        _RecordingProvider(
            [
                _keyed_calibration_packet(),
                _keyed_candidate_packet(violated="claim:limit"),
            ]
        )
    )

    assert result["semantic_judge_calibrated"] is True
    assert result["candidate_status"] == "FAIL"
    assert result["candidate_claim_status_counts"]["VIOLATED"] == 1
    assert result["candidate_claim_assessments"] == [
        {
            "claim_id_hash": stable_hash("claim:definition"),
            "status": "SATISFIED",
            "decisive_excerpt_hash": stable_hash("candidate"),
        },
        {
            "claim_id_hash": stable_hash("claim:limit"),
            "status": "VIOLATED",
            "decisive_excerpt_hash": stable_hash("candidate"),
        },
    ]
    assert result["passed"] is False


def test_candidate_global_falsehood_blocks_satisfied_rubric_claims() -> None:
    result = _run(
        _RecordingProvider(
            [
                _keyed_calibration_packet(),
                _keyed_candidate_packet(document_status="FAIL"),
            ]
        )
    )

    assert result["semantic_judge_calibrated"] is True
    assert result["candidate_document_status"] == "FAIL"
    assert result["candidate_status"] == "FAIL"
    assert result["candidate_claim_status_counts"]["SATISFIED"] == 2
    assert result["passed"] is False


def test_keyed_candidate_schema_fails_closed_on_missing_claim() -> None:
    candidate = _keyed_candidate_packet()
    del candidate["assessments"]["candidate"]["claim_statuses"]["claim:limit"]

    with pytest.raises(
        ValueError,
        match="invalid hidden candidate_integrated semantic judgment",
    ):
        _run(
            _RecordingProvider(
                [
                    _keyed_calibration_packet(),
                    candidate,
                ]
            )
        )


def test_candidate_document_grounding_must_select_a_supplied_evidence_ref() -> None:
    candidate = _keyed_candidate_packet(document_status="FAIL")
    candidate["assessments"]["candidate"][
        "document_decisive_evidence_ref"
    ] = "invented:evidence:ref"

    with pytest.raises(
        ValueError,
        match="document status needs a valid decisive candidate evidence ref",
    ):
        _run(
            _RecordingProvider(
                [
                    _keyed_calibration_packet(),
                    candidate,
                ]
            )
        )


def test_candidate_grounding_must_select_a_supplied_evidence_ref() -> None:
    candidate = _keyed_candidate_packet()
    candidate["assessments"]["candidate"]["decisive_evidence_refs"][
        "claim:definition"
    ] = "invented:evidence:ref"

    with pytest.raises(
        ValueError,
        match="every claim needs a valid decisive candidate evidence ref",
    ):
        _run(
            _RecordingProvider(
                [
                    _keyed_calibration_packet(),
                    candidate,
                ]
            )
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

    assert (
        "assessments[2] status is inconsistent with document and claim assessments"
        in errors
    )


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


def test_semantic_judge_calibration_accepts_case_statuses_without_claim_rows() -> None:
    assert validate_theory_semantic_gold_judgment(
        _calibration_packet(),
        claim_ids=[],
        required_case_ids=CASE_IDS,
    ) == []

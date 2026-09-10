from __future__ import annotations

import json
from copy import deepcopy

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


def _keyed_calibration_packets(
    *, misclassify_second_case: bool = False
) -> list[dict[str, object]]:
    second_violated = "" if misclassify_second_case else "claim:limit"
    return [
        {
            "assessments": {
                MODEL_CASE_IDS[0]: {
                    "document_status": "PASS",
                    "document_decisive_evidence_ref": "case_0001:0:0",
                    "claim_statuses": {
                        claim_id: "SATISFIED" for claim_id in CLAIM_IDS
                    },
                    "decisive_evidence_refs": {
                        claim_id: "case_0001:0:0" for claim_id in CLAIM_IDS
                    },
                },
            }
        },
        {
            "assessments": {
                MODEL_CASE_IDS[1]: {
                    "document_status": (
                        "PASS" if misclassify_second_case else "FAIL"
                    ),
                    "document_decisive_evidence_ref": "case_0002:0:0",
                    "claim_statuses": {
                        claim_id: (
                            "VIOLATED"
                            if claim_id == second_violated
                            else "SATISFIED"
                        )
                        for claim_id in CLAIM_IDS
                    },
                    "decisive_evidence_refs": {
                        claim_id: "case_0002:0:0" for claim_id in CLAIM_IDS
                    },
                },
            }
        },
    ]


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
    include_candidate_mode_negative: bool = False,
    candidate_is_reference: bool = False,
    activation_judgment: dict[str, object] | None = None,
    candidate_adjudication_strategy: str = "integrated_single",
) -> dict[str, object]:
    reference_documents = [
        {"path": "reference.md", "sha256": "reference", "content": "reference"}
    ]
    return run_theory_semantic_gold_judge(
        provider=provider,
        task_id="known-result",
        visible_question={"id": "known-result", "description": "derive it"},
        candidate_documents=(
            reference_documents
            if candidate_is_reference
            else [
                {
                    "path": "candidate.md",
                    "sha256": "candidate",
                    "content": "candidate",
                }
            ]
        ),
        reference_documents=reference_documents,
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
        candidate_mode_negative_cases=(
            [
                {
                    "case_id": "long-form-active-contradiction",
                    "expected_status": "FAIL",
                    "documents": [
                        {
                            "path": "long-form-near-miss.md",
                            "content": "A plausible conclusion with an active contradiction.",
                        }
                    ],
                }
            ]
            if include_candidate_mode_negative
            else []
        ),
        semantic_artifact_role=semantic_artifact_role,
        activation_judgment=activation_judgment,
        candidate_adjudication_strategy=candidate_adjudication_strategy,
    )


def test_semantic_gold_judge_requires_hidden_case_calibration() -> None:
    provider = _RecordingProvider(
        [*_keyed_calibration_packets(), _keyed_candidate_packet()]
    )

    result = _run(provider)

    assert result["protocol_version"] == 12
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
    assert result["n_model_calls"] == 3
    assert result["calibration_model_calls"] == 2
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
    assert len(provider.requests) == 3
    assert all(
        request.model == LIVE_EVALUATION_CLAUDE_MODEL
        for request in provider.requests
    )
    assert all(
        request.metadata["model_tier"] == "haiku"
        for request in provider.requests
    )
    assert "expected_status" not in provider.requests[0].user_prompt
    assert "Use PASS only when every required claim is established" in (
        provider.requests[0].system_prompt
    )
    assert "Use FAIL for a material active falsehood" in (
        provider.requests[0].system_prompt
    )
    assert "INCONCLUSIVE when support is absent or indeterminate" in (
        provider.requests[0].system_prompt
    )
    assert "Missing support is not itself a demonstrated contradiction" in (
        provider.requests[0].system_prompt
    )
    assert "active intermediate equations, assumptions, quantifiers and dependencies" in (
        provider.requests[0].system_prompt
    )
    assert "invalid asserted derivation" in provider.requests[0].system_prompt
    assert "Neither FAIL nor INCONCLUSIVE qualifies for acceptance" in provider.requests[0].system_prompt
    assert "unsupported source/result claims" not in provider.requests[0].system_prompt
    assert all(case_id not in provider.requests[0].user_prompt for case_id in CASE_IDS)
    assert "reference_complete.md" not in provider.requests[0].user_prompt
    assert "wrong_limit.md" not in provider.requests[0].user_prompt
    assert '"case_id": "candidate"' not in provider.requests[0].user_prompt
    assert all(case_id not in provider.requests[2].user_prompt for case_id in CASE_IDS)
    assert '"rubric_claim_ids": ["claim:definition", "claim:limit"]' in (
        provider.requests[0].user_prompt
    )
    assert '"claim:limit"' in provider.requests[2].user_prompt
    assert '"claim:definition"' in provider.requests[2].user_prompt
    assert result["calibration_claim_assessments_requested"] is True
    assert result["candidate_claim_assessments_requested"] is True
    for index, model_case_id in enumerate(MODEL_CASE_IDS):
        calibration_assessments = provider.requests[index].schema["properties"][
            "assessments"
        ]
        assert calibration_assessments["type"] == "object"
        assert calibration_assessments["required"] == [model_case_id]
        assert all(
            case_id not in json.dumps(provider.requests[index].schema)
            for case_id in CASE_IDS
        )
        calibration_schema = calibration_assessments["properties"][model_case_id]
        assert calibration_schema["required"] == [
            "document_status",
            "document_decisive_evidence_ref",
            "claim_statuses",
            "decisive_evidence_refs",
        ]
        assert calibration_schema["properties"]["claim_statuses"][
            "required"
        ] == CLAIM_IDS
    candidate_assessments = provider.requests[2].schema["properties"]["assessments"]
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
        "calibration"
    )
    assert provider.requests[2].metadata["semantic_adjudication_phase"] == (
        "candidate_integrated"
    )


def test_candidate_mode_negative_uses_exact_integrated_candidate_schema() -> None:
    provider = _RecordingProvider(
        [
            *_keyed_calibration_packets(),
            _keyed_candidate_packet(document_status="FAIL"),
            _keyed_candidate_packet(),
        ]
    )

    result = _run(provider, include_candidate_mode_negative=True)

    assert result["semantic_judge_calibrated"] is True
    assert result["passed"] is True
    assert result["n_model_calls"] == 4
    assert result["candidate_mode_negative_cases_configured"] is True
    assert result["candidate_mode_negative_case_ids_opaque"] is True
    assert result["candidate_mode_negative_claim_assessments_requested"] is True
    assert result["candidate_mode_negative_integrated_context"] is True
    assert result["candidate_mode_negative_model_calls"] == 1
    assert result["n_candidate_mode_negative_cases"] == 1
    assert result["n_candidate_mode_negative_cases_correct"] == 1
    assert result["candidate_mode_negative_controls_passed"] is True
    assert result["candidate_mode_negative_results"] == [
        {
            "case_id_hash": stable_hash("long-form-active-contradiction"),
            "observed_status": "FAIL",
            "correct": True,
        }
    ]
    negative_request = provider.requests[2]
    candidate_request = provider.requests[3]
    assert negative_request.metadata["semantic_adjudication_phase"] == (
        "candidate_mode_negative"
    )
    assert candidate_request.metadata["semantic_adjudication_phase"] == (
        "candidate_integrated"
    )
    assert negative_request.schema == candidate_request.schema
    assert "long-form-active-contradiction" not in negative_request.user_prompt
    assert "expected_status" not in negative_request.user_prompt
    assert '"case_id": "candidate"' in negative_request.user_prompt
    assert '"claim:definition"' in negative_request.user_prompt
    assert '"claim:limit"' in negative_request.user_prompt


@pytest.mark.parametrize("observed_status", ["PASS", "FAIL", "INCONCLUSIVE"])
def test_calibration_retains_observed_status_without_hidden_case_content(
    observed_status: str,
) -> None:
    packets = _keyed_calibration_packets()
    assessment = packets[1]["assessments"][MODEL_CASE_IDS[1]]
    assessment["document_status"] = observed_status
    claim_status = {"PASS": "SATISFIED", "FAIL": "VIOLATED", "INCONCLUSIVE": "INCONCLUSIVE"}[observed_status]
    assessment["claim_statuses"] = {claim_id: claim_status for claim_id in CLAIM_IDS}
    provider = _RecordingProvider([*packets, _keyed_candidate_packet()])

    result = _run(provider)

    assert result["calibration_results"][1] == {
        "case_id_hash": stable_hash(CASE_IDS[1]),
        "observed_status": observed_status,
        "correct": observed_status == "FAIL",
    }
    assert result["passed"] is (observed_status == "FAIL")
    assert result["n_model_calls"] == 3
    serialized = json.dumps(result["calibration_results"])
    assert all(case_id not in serialized for case_id in CASE_IDS)
    assert "expected_status" not in serialized
    assert "documents" not in serialized


def test_adversarial_candidate_pass_can_overturn_plausible_integrated_pass() -> None:
    calibration_packets = _keyed_calibration_packets()
    provider = _RecordingProvider(
        [
            calibration_packets[0],
            calibration_packets[0],
            calibration_packets[1],
            calibration_packets[1],
            _keyed_candidate_packet(),
            _keyed_candidate_packet(violated="claim:limit"),
        ]
    )

    result = _run(
        provider,
        candidate_adjudication_strategy="integrated_plus_adversarial",
    )

    assert result["protocol_version"] == 13
    assert result["candidate_adjudication_strategy"] == (
        "integrated_plus_adversarial"
    )
    assert result["semantic_judge_calibrated"] is True
    assert result["candidate_status"] == "FAIL"
    assert result["candidate_claim_status_counts"]["VIOLATED"] == 1
    assert result["passed"] is False
    assert result["n_model_calls"] == 6
    assert result["calibration_model_calls"] == 4
    assert result["candidate_integrated_model_calls"] == 2
    assert result["candidate_adversarial_model_calls"] == 1
    assert [
        request.metadata["semantic_adjudication_phase"]
        for request in provider.requests
    ] == [
        "calibration",
        "calibration_adversarial",
        "calibration",
        "calibration_adversarial",
        "candidate_integrated",
        "candidate_integrated_adversarial",
    ]
    assert "uncertainty must not be relabeled as contradiction" in (
        provider.requests[-1].system_prompt
    )


def test_candidate_pass_cannot_override_candidate_mode_negative_false_accept() -> None:
    result = _run(
        _RecordingProvider(
            [
                *_keyed_calibration_packets(),
                _keyed_candidate_packet(),
                _keyed_candidate_packet(),
            ]
        ),
        include_candidate_mode_negative=True,
    )

    assert result["n_candidate_mode_negative_cases_correct"] == 0
    assert result["candidate_mode_negative_controls_passed"] is False
    assert result["semantic_judge_calibrated"] is False
    assert result["candidate_status"] == "PASS"
    assert result["passed"] is False


@pytest.mark.parametrize("includes_observed_status", [True, False])
def test_frozen_activation_skips_requalification_and_judges_candidate_once(
    includes_observed_status: bool,
) -> None:
    activation = _run(
        _RecordingProvider(
            [
                *_keyed_calibration_packets(),
                _keyed_candidate_packet(document_status="FAIL"),
                _keyed_candidate_packet(),
            ]
        ),
        include_candidate_mode_negative=True,
        candidate_is_reference=True,
    )
    if not includes_observed_status:
        for field in ("calibration_results", "candidate_mode_negative_results"):
            for row in activation[field]:
                row.pop("observed_status")
        activation.pop("judgment_hash")
        activation["judgment_hash"] = stable_hash(activation)
    provider = _RecordingProvider([_keyed_candidate_packet()])

    result = _run(
        provider,
        include_candidate_mode_negative=True,
        activation_judgment=activation,
    )

    assert result["passed"] is True
    assert result["semantic_judge_calibrated"] is True
    assert result["calibration_reused_from_activation"] is True
    assert result["calibration_model_calls"] == 0
    assert result["candidate_mode_negative_model_calls"] == 0
    assert result["activation_model_calls"] == 4
    assert result["activation_judgment_hash"] == activation["judgment_hash"]
    for field in ("calibration_results", "candidate_mode_negative_results"):
        assert result[field] == activation[field]
    assert result["n_model_calls"] == 1
    assert len(provider.requests) == 1
    assert provider.requests[0].metadata["semantic_adjudication_phase"] == (
        "candidate_integrated"
    )


@pytest.mark.parametrize(
    ("previous_protocol", "strategy"),
    [(10, "integrated_single"), (11, "integrated_plus_adversarial")],
)
def test_previous_prompt_qualification_cannot_authorize_current_judge(
    previous_protocol: int,
    strategy: str,
) -> None:
    packets = [*_keyed_calibration_packets(), _keyed_candidate_packet()]
    if strategy == "integrated_plus_adversarial":
        packets = [packet for packet in packets for _ in range(2)]
    activation = _run(
        _RecordingProvider(packets),
        candidate_is_reference=True,
        candidate_adjudication_strategy=strategy,
    )
    activation["protocol_version"] = previous_protocol
    activation.pop("judgment_hash")
    activation["judgment_hash"] = stable_hash(activation)
    original = deepcopy(activation)
    provider = _RecordingProvider([])

    with pytest.raises(ValueError, match="activation judgment protocol_version mismatch"):
        _run(provider, activation_judgment=activation, candidate_adjudication_strategy=strategy)

    assert provider.requests == []
    assert activation == original


def test_candidate_pass_cannot_override_failed_calibration() -> None:
    result = _run(
        _RecordingProvider(
            [
                *_keyed_calibration_packets(misclassify_second_case=True),
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
        [*_keyed_calibration_packets(), _keyed_candidate_packet()]
    )

    result = _run(provider)

    assert result["artifact_kind"] == "HiddenTheorySemanticGoldJudgment"
    assert all(
        request.metadata["subsystem"] == "TheorySemanticGoldJudge"
        for request in provider.requests
    )


def test_semantic_judge_records_scientific_document_role() -> None:
    provider = _RecordingProvider(
        [*_keyed_calibration_packets(), _keyed_candidate_packet()]
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
                *_keyed_calibration_packets(),
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
                *_keyed_calibration_packets(),
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
                    *_keyed_calibration_packets(),
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
                    *_keyed_calibration_packets(),
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
                    *_keyed_calibration_packets(),
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

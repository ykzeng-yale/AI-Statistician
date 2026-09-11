from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.client_tool_loop import ClientToolExecutionResult
from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL,
    ClientToolCall,
    ClientToolTurnResponse,
)
from ai_statistician.theory_semantic_gold_judge import (
    run_theory_semantic_gold_judge,
    SEMANTIC_REVIEW_SUBMIT_TOOL,
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
    workspace_root: Path

    def __init__(self, packets: list[dict[str, object]]) -> None:
        self.packets = packets
        self.requests = []

    def generate(self, _request):
        raise AssertionError("gold must not fall back to one-shot generation")

    def generate_client_tool_turn(self, request):
        packet = deepcopy(self.packets[min(len(self.requests), len(self.packets) - 1)])
        packet.setdefault("review_markdown", "# Referee report\n\nSynthetic mechanism fixture, not mathematical evidence.")
        self.requests.append(SimpleNamespace(
            native=request, model=request.model, metadata=request.metadata,
            system_prompt=request.system_prompt, user_prompt=request.messages[0]["content"],
            schema=request.tools[-1].input_schema,
        ))
        call = ClientToolCall(str(len(self.requests)), SEMANTIC_REVIEW_SUBMIT_TOOL, packet)
        return ClientToolTurnResponse(
            content_blocks=({"type": "tool_use", "id": call.call_id, "name": call.name, "input": packet},),
            tool_calls=(call,), text="",
            provider=self.provider_name,
            model=request.model,
        )


@pytest.fixture(autouse=True)
def _private_reviewer_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(_RecordingProvider, "workspace_root", tmp_path, raising=False)


def _run(
    provider: _RecordingProvider,
    *,
    semantic_artifact_role: str = "theory",
    include_candidate_mode_negative: bool = False,
    candidate_is_reference: bool = False,
    activation_judgment: dict[str, object] | None = None,
    candidate_adjudication_strategy: str = "integrated_single",
    max_tokens: int = 6000,
    reference_content: str = "reference",
    visible_question: dict[str, object] | None = None,
) -> dict[str, object]:
    reference_documents = [
        {"path": "reference.md", "sha256": "reference", "content": reference_content}
    ]
    return run_theory_semantic_gold_judge(
        provider=provider,
        workspace_root=provider.workspace_root,
        task_id="known-result",
        visible_question=(visible_question if visible_question is not None else
                          {"id": "known-result", "description": "derive it"}),
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
        max_tokens=max_tokens,
    )


def test_semantic_gold_judge_requires_hidden_case_calibration() -> None:
    provider = _RecordingProvider(
        [*_keyed_calibration_packets(), _keyed_candidate_packet()]
    )

    result = _run(provider)

    assert result["protocol_version"] == 20
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
    assert result["n_model_calls"] == (3 if observed_status == "FAIL" else 2)
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

    assert result["protocol_version"] == 21
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


def test_candidate_is_not_run_after_candidate_mode_negative_false_accept() -> None:
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
    assert result["candidate_status"] == "NOT_RUN"
    assert result["candidate_claim_model_calls"] == 0
    assert result["n_model_calls"] == 3
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
    [(14, "integrated_single"), (15, "integrated_plus_adversarial"),
     (16, "integrated_single"), (17, "integrated_plus_adversarial")],
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


def test_candidate_is_not_run_after_failed_calibration() -> None:
    result = _run(
        _RecordingProvider(
            [
                *_keyed_calibration_packets(misclassify_second_case=True),
                _keyed_candidate_packet(),
            ]
        )
    )

    assert result["semantic_judge_calibrated"] is False
    assert result["candidate_status"] == "NOT_RUN"
    assert result["candidate_claim_model_calls"] == 0
    assert result["n_model_calls"] == 2
    assert result["passed"] is False
    assert result["n_calibration_cases_correct"] == 1


@pytest.mark.parametrize("semantic_artifact_role", ["theory", "source_replication_report"])
@pytest.mark.parametrize("strategy", ["integrated_single", "integrated_plus_adversarial"])
def test_first_failed_control_stops_later_reviews_and_preserves_private_records(
    semantic_artifact_role: str, strategy: str,
) -> None:
    first = _keyed_calibration_packets()[0]
    first["assessments"][MODEL_CASE_IDS[0]]["document_status"] = "INCONCLUSIVE"
    provider = _RecordingProvider([first])
    original = deepcopy(first)

    result = _run(
        provider, semantic_artifact_role=semantic_artifact_role,
        candidate_adjudication_strategy=strategy, include_candidate_mode_negative=True,
    )

    calls = 2 if strategy == "integrated_plus_adversarial" else 1
    assert len(provider.requests) == result["n_model_calls"] == calls
    assert result["n_calibration_cases"] == 2
    assert result["calibration_results"] == [{
        "case_id_hash": stable_hash(CASE_IDS[0]),
        "observed_status": "INCONCLUSIVE", "correct": False,
    }]
    assert result["candidate_mode_negative_results"] == []
    assert result["candidate_mode_negative_controls_passed"] is False
    assert result["candidate_mode_negative_model_calls"] == 0
    assert result["candidate_mode_negative_claim_assessments_requested"] is False
    assert result["candidate_mode_negative_integrated_context"] is False
    assert result["candidate_status"] == result["candidate_document_status"] == "NOT_RUN"
    assert result["candidate_claim_assessments"] == []
    assert set(result["candidate_claim_status_counts"].values()) == {0}
    assert result["candidate_claim_assessments_requested"] is False
    assert result["candidate_document_status_requested"] is False
    assert result["candidate_integrated_context"] is False
    assert result["candidate_adversarial_model_calls"] == 0
    assert result["passed"] is False
    assert first == original
    assert len(result["review_workspace_refs"]) == calls
    for ref in result["review_workspace_refs"]:
        audit = json.loads(Path(ref["path"]).read_text())
        assert audit["phase"].startswith("calibration")
        assert Path(audit["report_ref"]["path"]).is_file()
        assert audit["model_calls"] == 1

    frozen = deepcopy(result)
    unused_provider = _RecordingProvider([])
    with pytest.raises(ValueError, match="invalid hidden semantic activation judgment"):
        _run(
            unused_provider, activation_judgment=result,
            semantic_artifact_role=semantic_artifact_role,
            candidate_adjudication_strategy=strategy, include_candidate_mode_negative=True,
        )
    assert unused_provider.requests == []
    assert result == frozen


def test_changed_shared_tool_contract_invalidates_qualification_without_calls(monkeypatch) -> None:
    from dataclasses import replace
    import ai_statistician.theory_semantic_gold_judge as judge

    activation = _run(_RecordingProvider([
        *_keyed_calibration_packets(), _keyed_candidate_packet(),
    ]), candidate_is_reference=True)
    original_tools = judge.theory_document_client_tools()
    monkeypatch.setattr(judge, "theory_document_client_tools", lambda: (
        replace(original_tools[0], description=original_tools[0].description + " Changed contract."),
        *original_tools[1:],
    ))
    provider = _RecordingProvider([])
    with pytest.raises(ValueError, match="review_contract_hash mismatch"):
        _run(provider, activation_judgment=activation)
    assert provider.requests == []


def test_changed_submission_schema_invalidates_qualification_without_calls(monkeypatch) -> None:
    import ai_statistician.theory_semantic_gold_judge as judge

    activation = _run(_RecordingProvider([
        *_keyed_calibration_packets(), _keyed_candidate_packet(),
    ]), candidate_is_reference=True)
    frozen = deepcopy(activation)
    original_schema = judge._theory_semantic_gold_judge_schema

    def changed_schema(**kwargs):
        schema = original_schema(**kwargs)
        schema["description"] = "Changed submission contract."
        return schema

    monkeypatch.setattr(judge, "_theory_semantic_gold_judge_schema", changed_schema)
    provider = _RecordingProvider([])
    with pytest.raises(ValueError, match="review_contract_hash mismatch"):
        _run(provider, activation_judgment=activation)
    assert provider.requests == []
    assert activation == frozen


@pytest.mark.parametrize("changed", [
    "system_prompt", "adversarial_prompt", "temperature", "tool_choice",
    "thinking_budget_tokens", "disable_parallel_tool_use", "enable_prompt_caching",
    "submission_description", "submission_strict", "submission_terminal",
])
def test_changed_native_request_invalidates_qualification_before_provider(monkeypatch, changed) -> None:
    from dataclasses import replace
    import ai_statistician.theory_semantic_gold_judge as judge

    activation = _run(_RecordingProvider([
        *_keyed_calibration_packets(), _keyed_candidate_packet(),
    ]), candidate_is_reference=True)
    frozen = deepcopy(activation)
    original_request = judge._semantic_review_request

    def changed_request(**kwargs):
        request = original_request(**kwargs)
        if changed == "adversarial_prompt":
            return (replace(request, system_prompt=request.system_prompt + " Changed contract.")
                    if kwargs["phase"].endswith("_adversarial") else request)
        if changed.startswith("submission_"):
            attribute = changed.removeprefix("submission_")
            tools = tuple(
                replace(tool, **{attribute: "Changed contract." if attribute == "description" else False})
                if tool.name == SEMANTIC_REVIEW_SUBMIT_TOOL else tool
                for tool in request.tools
            )
            return replace(request, tools=tools)
        value = {
            "system_prompt": request.system_prompt + " Changed contract.",
            "temperature": 0.5, "tool_choice": "any", "thinking_budget_tokens": 1024,
            "disable_parallel_tool_use": False, "enable_prompt_caching": False,
        }[changed]
        return replace(request, **{changed: value})

    monkeypatch.setattr(judge, "_semantic_review_request", changed_request)
    provider = _RecordingProvider([])
    with pytest.raises(ValueError, match="review_contract_hash mismatch"):
        _run(provider, activation_judgment=activation)
    assert provider.requests == []
    assert activation == frozen


@pytest.mark.parametrize("changed", [
    "SEMANTIC_REVIEW_MAX_TURNS", "SEMANTIC_REVIEW_MAX_TOOL_CALLS",
    "SEMANTIC_REVIEW_MAX_NO_PROGRESS_TURNS", "seed", "replicates", "timeout_s",
])
def test_changed_execution_policy_invalidates_qualification_without_calls(monkeypatch, changed) -> None:
    import ai_statistician.theory_semantic_gold_judge as judge

    activation = _run(_RecordingProvider([
        *_keyed_calibration_packets(), _keyed_candidate_packet(),
    ]), candidate_is_reference=True)
    if changed in judge.SEMANTIC_REVIEW_SCRATCH_SETTINGS:
        monkeypatch.setitem(judge.SEMANTIC_REVIEW_SCRATCH_SETTINGS, changed,
                            judge.SEMANTIC_REVIEW_SCRATCH_SETTINGS[changed] + 1)
    else:
        monkeypatch.setattr(judge, changed, getattr(judge, changed) + 1)
    provider = _RecordingProvider([])
    with pytest.raises(ValueError, match="review_contract_hash mismatch"):
        _run(provider, activation_judgment=activation)
    assert provider.requests == []


@pytest.mark.parametrize("role", ["theory", "source_replication_report", "design_memo"])
@pytest.mark.parametrize("strategy", ["integrated_single", "integrated_plus_adversarial"])
def test_artifact_review_retains_full_project_context_without_owning_its_completion(role, strategy) -> None:
    packets = [*_keyed_calibration_packets(), _keyed_candidate_packet()]
    if strategy == "integrated_plus_adversarial":
        packets = [packet for packet in packets for _ in range(2)]
    provider = _RecordingProvider(packets)
    question = {
        "id": "known-result",
        "description": "Develop a method, implement it, run experiments and deliver a final report.",
        "task_intent": {"theory": "required", "scientific_code": "required", "empirical": "required"},
    }
    result = _run(provider, semantic_artifact_role=role, visible_question=question,
                  candidate_adjudication_strategy=strategy)

    assert result["passed"] is True  # Synthetic artifact verdict, not full-task evidence.
    assert len(provider.requests) == len(packets)
    for request in provider.requests:
        payload = json.loads(request.user_prompt)
        assert payload["task"]["semantic_artifact_role"] == role
        assert payload["task"]["visible_question"] == question
        assert [row["claim_id"] for row in payload["claim_rubric"]["claims"]] == CLAIM_IDS
        assert "candidate document set, not overall project completion" in request.system_prompt
        assert "The artifact-specific rubric defines the obligations of this review" in request.system_prompt
        assert "original question supplies context and target fidelity" in request.system_prompt
        assert "including one outside the rubric" in request.system_prompt
        assert "expected_status" not in request.user_prompt


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


def test_candidate_document_grounding_must_select_a_supplied_evidence_ref(tmp_path) -> None:
    candidate = _keyed_candidate_packet(document_status="FAIL")
    candidate["assessments"]["candidate"][
        "document_decisive_evidence_ref"
    ] = "invented:evidence:ref"

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
    incomplete = next(tmp_path.glob("candidate_integrated-*/incomplete.json"))
    assert "document status needs a valid decisive candidate evidence ref" in incomplete.read_text()


def test_candidate_grounding_must_select_a_supplied_evidence_ref(tmp_path) -> None:
    candidate = _keyed_candidate_packet()
    candidate["assessments"]["candidate"]["decisive_evidence_refs"][
        "claim:definition"
    ] = "invented:evidence:ref"

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
    incomplete = next(tmp_path.glob("candidate_integrated-*/incomplete.json"))
    assert "every claim needs a valid decisive candidate evidence ref" in incomplete.read_text()


def test_retained_gold_uses_documents_and_same_model_scratch_feedback(monkeypatch, tmp_path) -> None:
    source_attempts = []
    scratch_roots = []

    def scratch(**kwargs):
        code = kwargs["tool_input"]["code"]
        source_attempts.append(code)
        scratch_roots.append(kwargs["scratchpad"].sandbox_dir)
        failed = len(source_attempts) == 1
        return ClientToolExecutionResult(
            content={"ok": not failed, "raw_output": "UNFAMILIAR_ENVIRONMENT_ERROR" if failed else "EXACT_SECOND_OBSERVATION"},
            is_error=failed,
        ), {"source_hash": stable_hash(code)}

    monkeypatch.setattr("ai_statistician.theory_semantic_gold_judge.execute_theory_scratchpad_tool", scratch)

    class Reviewer(_RecordingProvider):
        candidate_turns = 0

        def generate_client_tool_turn(self, request):
            if request.metadata["semantic_adjudication_phase"] != "candidate_integrated":
                return super().generate_client_tool_turn(request)
            self.candidate_turns += 1
            serialized = json.dumps(request.messages)
            if self.candidate_turns == 1:
                payload = json.loads(request.messages[0]["content"])
                path = payload["document_catalog"][0]["path"]
                name, arguments = "read_theory_document", {"path": path, "line_start": 1, "line_end": 1}
            elif self.candidate_turns in (2, 3):
                assert "REFERENCE_DOCUMENT_BODY" in serialized
                if self.candidate_turns == 3:
                    assert "UNFAMILIAR_ENVIRONMENT_ERROR" in serialized
                name = "run_theory_scratchpad"
                arguments = {"language": "python", "dependencies": [], "code": f"print({self.candidate_turns})"}
            elif self.candidate_turns == 4:
                assert "EXACT_SECOND_OBSERVATION" in serialized
                name, arguments = SEMANTIC_REVIEW_SUBMIT_TOOL, _keyed_candidate_packet()
                arguments["review_markdown"] = ""
            else:
                assert "review_markdown must contain" in serialized
                return super().generate_client_tool_turn(request)
            call = ClientToolCall(f"candidate-{self.candidate_turns}", name, arguments)
            return ClientToolTurnResponse(
                content_blocks=({"type": "tool_use", "id": call.call_id, "name": name, "input": arguments},),
                tool_calls=(call,), text="", provider=self.provider_name, model=request.model,
            )

    provider = Reviewer([*_keyed_calibration_packets(), _keyed_candidate_packet()])
    result = _run(provider, reference_content="REFERENCE_DOCUMENT_BODY" * 150)

    assert result["passed"] is True
    assert result["n_model_calls"] == 7
    assert result["candidate_integrated_model_calls"] == 5
    assert source_attempts == ["print(2)", "print(3)"]
    assert all(tmp_path in path.parents for path in scratch_roots)
    assert len(set(scratch_roots)) == 1
    audit = json.loads(Path(result["review_workspace_refs"][-1]["path"]).read_text())
    assert len(audit["scratch_execution_refs"]) == 2
    report = Path(audit["report_ref"]["path"])
    assert report.suffix == ".md"
    assert report.read_text().startswith("# Referee report")
    assert "Referee report" not in json.dumps(result)


def test_referee_reads_complete_candidate_file_with_its_original_layout() -> None:
    content = "    INDENTED_SOURCE_MARKER\n\n\\begin{align}\n  a &= b \\\\\n\n  b &= c\n\\end{align}\n"

    class Reader(_RecordingProvider):
        def generate_client_tool_turn(self, request):
            if request.metadata["semantic_adjudication_phase"] == "candidate_integrated":
                if len(request.messages) == 1:
                    payload = json.loads(request.messages[0]["content"])
                    candidates = [row for row in payload["document_catalog"] if row.get("role") == "candidate"]
                    assert len(candidates) == 1, "the complete candidate must be a readable file, not JSON paragraph fragments"
                    assert "INDENTED_SOURCE_MARKER" not in request.messages[0]["content"]
                    assert all("content" not in row for row in payload["document_evidence_units"])
                    assert all(row["document_path"] == candidates[0]["path"] for row in payload["document_evidence_units"])
                    call = ClientToolCall("read-current-file", "read_theory_document", {
                        "path": candidates[0]["path"], "line_start": 1, "line_end": candidates[0]["line_count"],
                    })
                    return ClientToolTurnResponse(
                        content_blocks=({"type": "tool_use", "id": call.call_id, "name": call.name, "input": call.input},),
                        tool_calls=(call,), text="", provider=self.provider_name, model=request.model,
                    )
                observation = json.loads(request.messages[-1]["content"][0]["content"])
                assert observation["content"] == content.rstrip("\n")
                assert observation["content"].startswith("    INDENTED_SOURCE_MARKER")
            return super().generate_client_tool_turn(request)

    result = _run(Reader([*_keyed_calibration_packets(), _keyed_candidate_packet()]),
                  candidate_is_reference=True, reference_content=content)
    assert result["passed"] is True
    assert result["candidate_claim_assessments"][0]["decisive_excerpt_hash"] == stable_hash("    INDENTED_SOURCE_MARKER")
    audit = json.loads(Path(result["review_workspace_refs"][-1]["path"]).read_text())
    assert all(Path(reference["path"]).read_text() == content for reference in audit["document_refs"].values())


@pytest.mark.parametrize("content", [
    "    first\n\n\n  second\n", "first\r\n\r\nsecond\r\n",
    "first\u2028second\n\nlast\n", "\n\nfirst\n\n```text\n  second\n\n  third\n```\n",
])
def test_referee_citation_locations_match_full_document_reads(content) -> None:
    from ai_statistician.theory_semantic_gold_judge import _semantic_document_inputs
    from ai_statistician.theory_workspace import read_theory_document_lines

    documents, catalog, units = _semantic_document_inputs([], [{
        "case_id": "candidate", "documents": [{"path": "hidden_case_label.md", "content": content}],
    }])
    assert list(documents.values()) == [content]
    assert "hidden_case_label" not in json.dumps(catalog)
    for unit in units:
        observation, _ = read_theory_document_lines(
            documents, path=unit["document_path"], line_start=unit["line_start"], line_end=unit["line_end"],
        )
        assert observation["content"] == "\n".join(unit["content"].splitlines())
        assert unit["content"] in content


@pytest.mark.parametrize("changed", ["report", "session", "audit", "document"])
def test_modified_private_review_invalidates_activation_without_model_calls(changed) -> None:
    activation = _run(_RecordingProvider([*_keyed_calibration_packets(), _keyed_candidate_packet()]), candidate_is_reference=True)
    original = deepcopy(activation)
    audit_path = Path(activation["review_workspace_refs"][0]["path"])
    audit = json.loads(audit_path.read_text())
    session = audit["session_ref"]
    path = {"audit": audit_path, "report": Path(audit["report_ref"]["path"]),
            "document": Path(next(iter(audit["document_refs"].values()))["path"]),
            "session": Path(session["root_path"]) / session["relative_path"]}[changed]
    path.write_text("changed synthetic authority")
    provider = _RecordingProvider([])

    with pytest.raises(ValueError, match="activation review workspace invalid"):
        _run(provider, activation_judgment=activation)

    assert provider.requests == []
    assert activation == original


def test_review_sampling_contract_cannot_change_after_activation() -> None:
    activation = _run(_RecordingProvider([*_keyed_calibration_packets(), _keyed_candidate_packet()]), candidate_is_reference=True)
    provider = _RecordingProvider([])

    with pytest.raises(ValueError, match="review_contract_hash mismatch"):
        _run(provider, activation_judgment=activation, max_tokens=7000)

    assert provider.requests == []


def test_review_workspaces_are_isolated_and_tool_use_is_not_mandatory() -> None:
    provider = _RecordingProvider([*_keyed_calibration_packets(), _keyed_candidate_packet()])
    result = _run(provider)
    assert result["passed"] is True
    roots = []
    for request, reference in zip(provider.requests, result["review_workspace_refs"]):
        assert len(request.native.messages) == 1
        assert request.native.tool_choice == "auto"
        assert request.native.thinking_budget_tokens == 0
        assert {tool.name for tool in request.native.tools} == {
            "read_theory_document", "search_theory_documents", "run_theory_scratchpad", SEMANTIC_REVIEW_SUBMIT_TOOL,
        }
        audit = json.loads(Path(reference["path"]).read_text())
        roots.append(audit["session_ref"]["root_path"])
        assert audit["model_calls"] == 1
        assert audit["scratch_execution_refs"] == []
    assert len(set(roots)) == 3


def test_gold_cannot_fall_back_to_tool_free_provider(monkeypatch) -> None:
    provider = _RecordingProvider([])
    monkeypatch.setattr(provider, "generate_client_tool_turn", None)
    with pytest.raises(ValueError, match="requires native client-tool turns"):
        _run(provider)
    assert provider.requests == []


def test_gold_cannot_write_hidden_reviews_into_product_repository(monkeypatch) -> None:
    provider = _RecordingProvider([])
    monkeypatch.setattr(provider, "workspace_root", Path(__file__).resolve().parents[1] / "runs" / "forbidden_gold")
    with pytest.raises(ValueError, match="outside the product repository"):
        _run(provider)
    assert provider.requests == []


@pytest.mark.parametrize(("language", "source"), [("python", "print(7)"), ("r", "cat(7)")])
def test_gold_executes_real_scientific_sandbox_without_live_provider(language, source) -> None:
    class Reviewer(_RecordingProvider):
        def generate_client_tool_turn(self, request):
            if request.metadata["semantic_adjudication_phase"] == "candidate_integrated":
                if len(request.messages) == 1:
                    arguments = {"language": language, "dependencies": [], "code": source}
                    call = ClientToolCall("scratch", "run_theory_scratchpad", arguments)
                    return ClientToolTurnResponse(
                        content_blocks=({"type": "tool_use", "id": call.call_id, "name": call.name, "input": arguments},),
                        tool_calls=(call,), text="", provider=self.provider_name, model=request.model,
                    )
                observation = json.loads(request.messages[-1]["content"][0]["content"])
                assert observation["execution_attempted"] is True
                assert observation["returncode"] == 0
                assert observation["runtime_edited_source"] is False
            return super().generate_client_tool_turn(request)

    result = _run(Reviewer([*_keyed_calibration_packets(), _keyed_candidate_packet()]))
    audit = json.loads(Path(result["review_workspace_refs"][-1]["path"]).read_text())
    scratch = audit["scratch_execution_refs"][0]
    assert scratch["language"] == language
    assert scratch["code_hash"] == stable_hash(source)
    assert Path(scratch["code_path"]).read_text() == source
    assert result["n_model_calls"] == 4


def test_plain_text_stop_preserves_incomplete_private_session_without_acceptance(tmp_path) -> None:
    class Reviewer(_RecordingProvider):
        def generate_client_tool_turn(self, request):
            if request.metadata["semantic_adjudication_phase"] == "candidate_integrated":
                return ClientToolTurnResponse(
                    content_blocks=({"type": "text", "text": "Still unresolved."},),
                    tool_calls=(), text="Still unresolved.", provider=self.provider_name, model=request.model,
                )
            return super().generate_client_tool_turn(request)

    provider = Reviewer(_keyed_calibration_packets())
    with pytest.raises(ValueError, match="without a client tool call"):
        _run(provider)
    workspace = next(tmp_path.glob("candidate_integrated-*"))
    assert (workspace / "incomplete.json").is_file()
    assert not (workspace / "review.md").exists()
    transcripts = list(workspace.rglob("*.json"))
    assert any("Still unresolved." in path.read_text() for path in transcripts)
    assert len(provider.requests) == 2


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

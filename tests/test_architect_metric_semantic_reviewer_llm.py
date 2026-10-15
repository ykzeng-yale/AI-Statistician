from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from ai_statistician.architect_metric_contract_authoring import (
    ArchitectMetricContractAuthoringConfig,
    METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
    METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
    METRIC_PROTOCOL_WORKSPACE_READ_TOOL,
    METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT,
    _compact_metric_authoring_prompt_payload,
    author_reviewed_architect_metric_requirements,
)
from ai_statistician.architect_metric_semantic_reviewer_llm import (
    ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA,
    ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE,
    ArchitectMetricSemanticReviewerConfig,
    LLMArchitectMetricSemanticReviewerAgent,
    architect_metric_review_material_with_runtime_evaluator_certificate,
    architect_metric_semantic_review_json_schema,
    bind_architect_metric_finding_evidence_identities,
    build_architect_metric_semantic_review_prompt,
    validate_architect_metric_semantic_review_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.metric_protocol_stage import METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED
from ai_statistician.generated_metric_contract import (
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_set_id,
)
from ai_statistician.model_backend import ClientToolCall, ClientToolTurnResponse
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.packet_validation import PacketValidationError
from ai_statistician.theory_workspace import (
    THEORY_SCRATCHPAD_TOOL,
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    THEORY_WORKSPACE_HANDOFF_ROLE,
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    TheoryScratchpadConfig,
    theory_workspace_document_manifest,
)


TEST_HAIKU_MODEL = "claude-haiku-4-5-20251001"
TEST_LOCAL_MODEL = "Qwen3-4B-Instruct-2507"


def _requirement(
    requirement_id: str = "generic_gate",
    **overrides: object,
) -> dict[str, object]:
    row: dict[str, object] = {
        "requirement_id": requirement_id,
        "target_subsystems": ["SimulationEngineer"],
        "metric_semantics": "one raw finite generic diagnostic",
        "metric_value_kind": "numeric",
        "measurement_protocol": "return one raw generic diagnostic value",
        "required_runtime_replicates": 20,
        "operator": "<=",
        "threshold": 0.1,
        "lower": None,
        "upper": None,
        "tolerance": 0.0,
        "aggregation": "identity",
        "minimum_pass_count": None,
        "minimum_pass_fraction": None,
        "required": True,
        "source_anchors": [f"theory:{requirement_id}"],
        "boundary": "pre-execution empirical control, not proof evidence",
    }
    row.update(overrides)
    return row


def _material(
    *,
    requirements: list[dict[str, object]] | None = None,
    prior_ledger: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    requirements = requirements or [_requirement()]
    anchors = [
        {
            "anchor_id": str(requirement["source_anchors"][0]),
            "content": {
                "threshold": requirement["threshold"],
                "metric_semantics": requirement["metric_semantics"],
            },
        }
        for requirement in requirements
    ]
    material: dict[str, object] = {
        "review_stage": "pre_execution_metric_contract_review",
        "execution_results_available": False,
        "model_authored_runtime_replicates": 20,
        "runtime_execution_capacity": {
            "max_runtime_replicates": 100_000,
            "timeout_seconds": 60,
        },
        "metric_evaluation_semantics": (
            generated_metric_evaluation_semantics_contract()
        ),
        "empirical_metric_requirements": requirements,
        "acceptance_authority_catalog_id": "catalog:generic",
        "acceptance_authority_catalog": anchors,
        "accepted_implementation_interface_handoff": {
            "handoff_id": "implementation:generic",
            "question_id": "q_metric_review",
            "theory_packet_id": "theory:packet",
            "implementation_interfaces": [
                {
                    "estimator_id": "estimator:generic",
                    "response_fields": [{"name": "diagnostic"}],
                }
            ],
            "runtime_selected_semantics": False,
            "proof_evidence_status": "NOT_PROOF_EVIDENCE",
        },
        "theory_developer_protocol_material": {
            "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
            "source_theory_packet_id": "theory:packet",
            "source_theory_packet_hash": stable_hash({"theory": 1}),
            "execution_results_available": False,
            "theory_semantic_material": {
                "problem_card": {
                    "estimand": "theta",
                    "dgp": "generic finite observation",
                },
                "estimator_specs": [
                    {
                        "id": "estimator:generic",
                        "formula": "theta_hat",
                        "normalization": "identity",
                        "sample_size_order": "O(1)",
                    }
                ],
                "simulation_ademp_spec": {
                    "aim": "measure the diagnostic before acceptance"
                },
            },
        },
        "upstream_research_contract": {
            "simulation_targets": ["measure the diagnostic"]
        },
        "active_prior_finding_ledger": list(prior_ledger or []),
    }
    return architect_metric_review_material_with_runtime_evaluator_certificate(
        material
    )


def _payload(
    requirements: list[dict[str, object]],
    *,
    status: str = "PASS",
    findings: list[dict[str, object]] | None = None,
    prior_reviews: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "requirement_reviews": {
            str(requirement["requirement_id"]): {
                "status": status,
                "semantic_positive_control": {
                    "raw_comparison_value": 0.0,
                    "rationale": (
                        "The cited scientific target treats zero as a valid "
                        "positive-control diagnostic."
                    ),
                    "evidence_refs": [
                        f"requirement:{requirement['requirement_id']}",
                        str(requirement["source_anchors"][0]),
                    ],
                },
                "rationale": (
                    "The frozen scalar measurement, normalization, operator, "
                    "and cited threshold agree."
                ),
                "evidence_refs": [
                    f"requirement:{requirement['requirement_id']}",
                    str(requirement["source_anchors"][0]),
                ],
            }
            for requirement in requirements
        },
        "portfolio_review": {
            "status": status,
            "rationale": (
                "The required rows jointly measure the requested empirical "
                "target without redundant scenario-specific gates."
            ),
            "evidence_refs": [
                f"requirement:{requirement['requirement_id']}"
                for requirement in requirements
            ],
        },
        "prior_finding_reviews": list(prior_reviews or []),
        "findings": list(findings or []),
    }


def _finding(
    requirement_id: str = "generic_gate",
    *,
    prior_finding_id: str = "",
) -> dict[str, object]:
    return {
        "prior_finding_id": prior_finding_id,
        "new_finding_rationale": (
            "" if prior_finding_id else "This defect is new in the current row."
        ),
        "severity": "high",
        "category": "measurement_alignment",
        "summary": "The measurement does not identify the requested target.",
        "observed_behavior": "The row measures a different scalar.",
        "expected_behavior": "The row must measure the frozen target scalar.",
        "evidence_refs": [f"requirement:{requirement_id}"],
    }


class _Backend:
    provider_name = "anthropic"

    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.requests = []

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        payload = self.payload(request) if callable(self.payload) else self.payload
        call = ClientToolCall(
            call_id=f"metric-review-{len(self.requests)}",
            name="submit_architect_metric_semantic_review",
            input=payload,
        )
        return ClientToolTurnResponse(
            content_blocks=(
                {
                    "type": "tool_use",
                    "id": call.call_id,
                    "name": call.name,
                    "input": payload,
                },
            ),
            tool_calls=(call,),
            text="",
            provider="anthropic",
            model=request.model,
            metadata={"provider_stop_reason": "tool_use"},
        )


def _review(
    payload: object,
    *,
    material: dict[str, object] | None = None,
    source_agent: str = "ArchitectMetricContractPlanner",
    theory_scratchpad: TheoryScratchpadConfig | None = None,
) -> tuple[dict[str, object], _Backend, dict[str, object]]:
    material = material or _material()
    backend = _Backend(payload)
    theory = material["theory_developer_protocol_material"]
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=TEST_HAIKU_MODEL,
            model_tier="haiku",
        ),
    ).review(
        question=OpenResearchQuestion(
            id="q_metric_review",
            title="Review a generic statistical protocol",
            description="Assess a frozen empirical procedure.",
        ),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:1",
            "authoring_packet_hash": stable_hash({"candidate": 1}),
            "empirical_metric_requirement_set_id": (
                generated_metric_requirement_set_id(
                    material["empirical_metric_requirements"]
                )
            ),
            "source_agent": source_agent,
            "source_model": TEST_HAIKU_MODEL,
            "source_model_tier": "haiku",
            "source_theory_packet_id": theory["source_theory_packet_id"],
            "source_theory_packet_hash": theory["source_theory_packet_hash"],
            "acceptance_authority_catalog_id": (
                material["acceptance_authority_catalog_id"]
            ),
            "acceptance_authority_catalog_fingerprint": stable_hash(
                material["acceptance_authority_catalog"]
            ),
        },
        theory_scratchpad=theory_scratchpad,
    )
    return packet, backend, material


def test_compact_reviewer_accepts_exact_frozen_requirements_in_one_call() -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]

    packet, backend, _ = _review(_payload(requirements), material=material)
    assert backend.requests[0].tool_choice == "any"
    assert [tool.name for tool in backend.requests[0].tools] == ["submit_architect_metric_semantic_review"]

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["reviewed_requirement_ids"] == ["generic_gate"]
    assert packet["runtime_evaluator_certificate_all_rows_schema_valid"] is True
    assert packet["independent_agent"] is True
    assert packet["independent_invocation"] is True
    assert packet["proof_evidence_status"] == (
        ARCHITECT_METRIC_SEMANTIC_REVIEW_NOT_PROOF_EVIDENCE
    )
    assert len(backend.requests) == 1
    assert backend.requests[0].metadata["full_packet_regeneration_disabled"] is True
    assert backend.requests[0].metadata["strict_terminal_tool_schema"] is True
    assert backend.requests[0].metadata["reviewer_local_retry_budget"] is False
    assert backend.requests[0].tools[-1].strict is True
    assert "claim_checks" not in packet
    assert "response_identity_checks" not in packet
    assert "dimension_reviews" not in packet


def test_metric_reviewer_rejects_one_shot_transport() -> None:
    class GeneratorOnlyBackend:
        provider_name = "anthropic"

    reviewer = LLMArchitectMetricSemanticReviewerAgent(
        provider=GeneratorOnlyBackend(),
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=TEST_HAIKU_MODEL,
            model_tier="haiku",
        ),
    )

    with pytest.raises(ValueError, match="native client-tool turns"):
        reviewer.review(
            question=OpenResearchQuestion(
                id="q_metric_review",
                title="Review transport",
                description="Require one persistent reviewer session.",
            ),
            review_material={},
            trusted_lineage={},
        )


def test_metric_reviewer_recomputes_in_same_session_scratch(
    tmp_path,
) -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]
    submission = _payload(
        requirements,
        status="FAIL",
        findings=[_finding()],
    )
    submission["requirement_reviews"]["generic_gate"]["rationale"] = (
        "Scratch recomputation gives the finite-population sample variance "
        "82.5 / 9 = 9.166666666666666, contradicting the cited constant."
    )

    class ScratchThenSubmitBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.observed_scratch = ""

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) <= 4:
                name = THEORY_SCRATCHPAD_TOOL
                payload = {
                    "language": "python",
                    "dependencies": [],
                    "code": (
                        "xs = list(range(10))\n"
                        "mean = sum(xs) / len(xs)\n"
                        "value = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)\n"
                        "print({'sample_variance': value})\n"
                    ),
                }
            else:
                self.observed_scratch = json.dumps(
                    request.messages, sort_keys=True, default=str
                )
                name = "submit_architect_metric_semantic_review"
                payload = submission
            call = ClientToolCall(
                call_id=f"metric-review-{len(self.requests)}",
                name=name,
                input=payload,
            )
            return ClientToolTurnResponse(
                content_blocks=(
                    {
                        "type": "tool_use",
                        "id": call.call_id,
                        "name": name,
                        "input": payload,
                    },
                ),
                tool_calls=(call,),
                text="",
                provider="anthropic",
                model=request.model,
                metadata={"provider_stop_reason": "tool_use"},
            )

    backend = ScratchThenSubmitBackend()
    theory = material["theory_developer_protocol_material"]
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="anthropic",
            model=TEST_HAIKU_MODEL,
            model_tier="haiku",
        ),
    ).review(
        question=OpenResearchQuestion(
            id="q_metric_review",
            title="Review a generic statistical protocol",
            description="Assess a frozen empirical procedure.",
        ),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "metric-authoring:1",
            "authoring_packet_hash": stable_hash({"candidate": 1}),
            "empirical_metric_requirement_set_id": (
                generated_metric_requirement_set_id(requirements)
            ),
            "source_agent": "ArchitectMetricContractPlanner",
            "source_model": TEST_HAIKU_MODEL,
            "source_model_tier": "haiku",
            "source_theory_packet_id": theory["source_theory_packet_id"],
            "source_theory_packet_hash": theory["source_theory_packet_hash"],
            "acceptance_authority_catalog_id": material[
                "acceptance_authority_catalog_id"
            ],
            "acceptance_authority_catalog_fingerprint": stable_hash(
                material["acceptance_authority_catalog"]
            ),
        },
        theory_scratchpad=TheoryScratchpadConfig(
            sandbox_dir=tmp_path,
            seed=17,
            replicates=20,
        ),
    )

    assert packet["overall_verdict"] == "REVISE"
    assert "9.166666666666666" in backend.observed_scratch
    refs = packet["client_tool_loop"]["scratch_execution_refs"]
    assert len(refs) == 4
    assert all(ref["status"] == "EXECUTED" for ref in refs)
    assert all(ref["invocation_mode"] == "script" for ref in refs)
    assert packet["client_tool_loop"]["runtime_executed_tool_calls"] == 5


def test_metric_reviewer_receives_submission_validation_in_same_session() -> None:
    requirements = [_requirement("gate_one"), _requirement("gate_two")]
    material = _material(requirements=requirements)
    responses = iter([_payload(requirements[:1]), _payload(requirements)])

    packet, backend, _ = _review(lambda request: next(responses), material=material)

    assert packet["overall_verdict"] == "ACCEPT"
    assert len(backend.requests) == 2
    assert "exact ordered frozen requirement IDs" in json.dumps(
        backend.requests[1].messages, default=str
    )
    assert packet["client_tool_loop"]["validation_submissions"] == 2
    assert packet["client_tool_loop"]["validation_feedback_observed"] is True


def test_metric_reviewer_returns_every_validator_observation_to_same_session() -> None:
    requirements = [_requirement("generic_gate")]
    material = _material(requirements=requirements)
    invalid = _payload(
        requirements,
        findings=[
            {
                "prior_finding_id": "",
                "new_finding_rationale": "",
                "severity": "invalid",
                "category": "",
                "summary": "",
                "observed_behavior": "",
                "expected_behavior": "",
                "evidence_refs": [],
            }
            for _ in range(14)
        ],
    )
    responses = iter([invalid, _payload(requirements)])

    packet, backend, _ = _review(
        lambda request: next(responses),
        material=material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    observed = json.dumps(backend.requests[1].messages, default=str)
    assert "findings[0] has invalid severity" in observed
    assert "findings[13] missing evidence_refs" in observed
    first_history = packet["client_tool_loop"][
        "validation_submission_history"
    ][0]
    assert len(first_history["errors"]) > 12


def test_metric_reviewer_requires_complete_resubmission_after_validation_feedback() -> None:
    requirements = [_requirement("gate_one"), _requirement("gate_two")]
    material = _material(requirements=requirements)
    complete = _payload(requirements)
    responses = iter(
        [
            {"requirement_reviews": complete["requirement_reviews"]},
            complete,
        ]
    )

    packet, backend, _ = _review(
        lambda request: next(responses),
        material=material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["reviewed_requirement_ids"] == ["gate_one", "gate_two"]
    assert len(backend.requests) == 2
    second_request = json.dumps(backend.requests[1].messages, default=str)
    assert "complete corrected judgment" in second_request.lower()
    loop = packet["client_tool_loop"]
    assert loop["strict_terminal_tool_schema"] is True
    assert loop["validation_submissions"] == 2
    assert loop["transport"] == "native_same_reviewer_session_v2"
    history = loop["validation_submission_history"]
    assert history[0]["ok"] is False
    assert history[1]["ok"] is True
    assert "draft_fingerprint" not in history[0]


def test_metric_reviewer_does_not_retain_an_invalid_partial_judgment() -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]
    incomplete = _payload(requirements)
    incomplete["portfolio_review"]["status"] = ""
    responses = iter(
        [
            incomplete,
            _payload(requirements),
        ]
    )

    packet, _, _ = _review(
        lambda request: next(responses),
        material=material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["portfolio_review"]["status"] == "PASS"
    assert packet["portfolio_review"]["rationale"] == (
        _payload(requirements)["portfolio_review"]["rationale"]
    )
    assert packet["client_tool_loop"]["validation_submission_history"][0][
        "ok"
    ] is False


def test_compact_reviewer_derives_revise_from_model_judgments() -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]

    packet, _, _ = _review(
        _payload(
            requirements,
            status="FAIL",
            findings=[_finding()],
        ),
        material=material,
    )

    assert packet["overall_verdict"] == "REVISE"
    assert packet["requirement_reviews"][0]["status"] == "FAIL"
    assert packet["findings"][0]["finding_id"].startswith(
        "metric_protocol_finding:"
    )


def test_runtime_positive_control_rejects_an_implicit_target_shift() -> None:
    requirement = _requirement(
        metric_semantics=(
            "absolute realized fraction whose scientific target is 0.30"
        ),
        measurement_protocol="return the absolute realized fraction",
        operator="between",
        threshold=None,
        lower=-0.05,
        upper=0.05,
        tolerance=0.01,
        aggregation="mean",
    )
    material = _material(requirements=[requirement])
    payload = _payload([requirement])
    payload["requirement_reviews"]["generic_gate"][
        "semantic_positive_control"
    ] = {
        "raw_comparison_value": 0.30,
        "rationale": "The cited scientific target is an absolute fraction of 0.30.",
        "evidence_refs": ["requirement:generic_gate", "theory:generic_gate"],
    }

    packet, _, _ = _review(payload, material=material)

    review = packet["requirement_reviews"][0]
    control = review["semantic_positive_control"]["runtime_evaluation"]
    assert review["status"] == "PASS"
    assert review["semantic_control_status"] == "CONTRADICTION"
    assert control["raw_comparison_value"] == pytest.approx(0.30)
    assert control["runtime_passed"] is False
    assert control["runtime_matches_scientific_expectation"] is False
    assert packet["overall_verdict"] == "REVISE"
    assert packet["validation_errors"] == []


def test_compact_reviewer_rejects_missing_requirement_coverage() -> None:
    requirements = [_requirement("gate_one"), _requirement("gate_two")]
    material = _material(requirements=requirements)
    incomplete = _payload(requirements[:1])

    with pytest.raises(PacketValidationError) as exc_info:
        _review(incomplete, material=material)

    assert "exact ordered frozen requirement IDs" in str(exc_info.value)


def test_compact_reviewer_rejects_nonpass_without_typed_finding() -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]

    with pytest.raises(PacketValidationError) as exc_info:
        _review(
            _payload(requirements, status="UNCERTAIN"),
            material=material,
        )

    assert "requires one medium, high, or critical finding" in str(
        exc_info.value
    )


def test_compact_reviewer_requires_independent_agent_for_acceptance() -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]

    with pytest.raises(PacketValidationError) as exc_info:
        _review(
            _payload(requirements),
            material=material,
            source_agent="LLMArchitectMetricSemanticReviewerAgent",
        )

    assert "ACCEPT requires an independent reviewer agent" in str(
        exc_info.value
    )


def test_prior_finding_identity_is_reviewed_without_replaying_old_packets() -> None:
    prior_id = "metric_protocol_finding:prior"
    material = _material(
        prior_ledger=[
            {
                "finding_id": prior_id,
                "status": "ACTIVE",
                "finding": {
                    "severity": "high",
                    "category": "measurement_alignment",
                    "summary": "Prior measurement mismatch.",
                    "observed_behavior": "Wrong scalar.",
                    "expected_behavior": "Target scalar.",
                    "evidence_refs": ["requirement:generic_gate"],
                },
            }
        ]
    )
    requirements = material["empirical_metric_requirements"]
    prior_reviews = [
        {
            "finding_id": prior_id,
            "status": "UNRESOLVED",
            "runtime_contract_evidence_id": "",
            "rationale": "The current row still measures the wrong scalar.",
        }
    ]

    packet, _, _ = _review(
        _payload(
            requirements,
            status="FAIL",
            findings=[_finding(prior_finding_id=prior_id)],
            prior_reviews=prior_reviews,
        ),
        material=material,
    )

    assert packet["overall_verdict"] == "REVISE"
    assert packet["expected_prior_finding_ids"] == [prior_id]
    assert packet["findings"][0]["finding_id"] == prior_id


def test_runtime_contract_retraction_requires_exact_certificate_id() -> None:
    prior_id = "metric_protocol_finding:prior"
    material = _material(
        prior_ledger=[
            {
                "finding_id": prior_id,
                "status": "ACTIVE",
                "finding": {"summary": "Prior runtime interpretation mismatch."},
            }
        ]
    )
    requirements = material["empirical_metric_requirements"]
    payload = _payload(
        requirements,
        prior_reviews=[
            {
                "finding_id": prior_id,
                "status": "RETRACTED_RUNTIME_CONTRACT_CONFLICT",
                "runtime_contract_evidence_id": "made-up-certificate",
                "rationale": "The runtime contract resolves the interpretation.",
            }
        ],
    )

    with pytest.raises(PacketValidationError) as exc_info:
        _review(payload, material=material)

    assert "invalid runtime retraction evidence" in str(exc_info.value)


def test_prompt_projects_semantic_inputs_without_long_derivation_replay() -> None:
    material = _material()
    semantic = material["theory_developer_protocol_material"][
        "theory_semantic_material"
    ]
    semantic["theorem_cards"] = [
        {"id": "theorem:secret", "conclusion": "OMIT_LONG_THEOREM"}
    ]
    semantic["lemma_cards"] = [
        {"id": "lemma:secret", "statement": "OMIT_LONG_LEMMA"}
    ]
    semantic["theory_derivation_packet"] = {
        "derivation_summary": "retain this summary",
        "assumption_ledger": [{"assumption": "retain this assumption"}],
        "derivation_steps": [
            {"id": "step:secret", "claim": "OMIT_LONG_DERIVATION"}
        ],
        "equation_chain": [{"lhs": "OMIT_LONG_EQUATION"}],
    }

    prompt = build_architect_metric_semantic_review_prompt(
        question=OpenResearchQuestion(
            id="q_metric_review",
            title="Generic review",
            description="Review compactly.",
        ),
        review_material=material,
    )
    payload = json.loads(prompt.split("\n\n", 1)[1])

    assert "retain this summary" in prompt
    assert "retain this assumption" in prompt
    assert "OMIT_LONG_THEOREM" not in prompt
    assert "OMIT_LONG_LEMMA" not in prompt
    assert "OMIT_LONG_DERIVATION" not in prompt
    assert "OMIT_LONG_EQUATION" not in prompt
    assert "metric_claim_check_contract" not in prompt
    assert "substitute the declared raw metric" in prompt
    assert "Independently recompute every load-bearing constant" in prompt
    assert "Runtime resource limits are not scientific justification" in prompt
    assert "actual comparison scale" in prompt
    assert "Required rows must correspond to distinct upstream claims" in prompt
    assert "runtime applies no hidden centering" in prompt
    assert "semantic_positive_control" in prompt
    assert "implicit_transformations_applied" in prompt
    assert payload["review_material"]["model_authored_runtime_replicates"] == 20
    assert payload["review_material"]["runtime_execution_capacity"] == {
        "max_runtime_replicates": 100_000,
        "timeout_seconds": 60,
    }
    comparison = payload["review_material"]["runtime_evaluator_certificate"][
        "certificates"
    ][0]["comparison_stage"]
    assert comparison["operator"] == "<="
    assert comparison["threshold"] == 0.1
    assert len(prompt) < 30_000


def test_dynamic_schema_is_small_and_provider_transformable() -> None:
    material = _material(
        requirements=[
            _requirement(f"gate_{index}") for index in range(8)
        ],
        prior_ledger=[
            {
                "finding_id": "finding:one",
                "finding": {"summary": "one"},
            }
        ],
    )
    schema = architect_metric_semantic_review_json_schema(material)

    assert len(json.dumps(schema, separators=(",", ":"))) < 8_000
    requirement_schema = schema["properties"]["requirement_reviews"]
    assert requirement_schema["required"] == [
        f"gate_{index}" for index in range(8)
    ]
    assert set(requirement_schema["properties"]) == set(
        requirement_schema["required"]
    )
    assert requirement_schema["additionalProperties"] is False
    assert all(
        value == {"$ref": "#/$defs/requirement_review"}
        for value in requirement_schema["properties"].values()
    )
    requirement_properties = schema["$defs"]["requirement_review"][
        "properties"
    ]
    assert requirement_properties["semantic_positive_control"]["properties"][
        "raw_comparison_value"
    ] == {"anyOf": [{"type": "number"}, {"type": "boolean"}]}
    assert schema["properties"]["prior_finding_reviews"]["minItems"] == 1
    assert "maxItems" not in schema["properties"]["findings"]
    assert "maxItems" not in requirement_properties["evidence_refs"]
    assert "maxLength" not in requirement_properties["rationale"]
    assert "claim_checks" not in schema["properties"]
    assert "response_identity_checks" not in schema["properties"]
    assert "dimension_reviews" not in schema["properties"]

    anthropic = pytest.importorskip("anthropic")
    transformed = anthropic.transform_schema(schema)
    assert transformed["type"] == "object"
    transformed_requirement_schema = transformed["properties"][
        "requirement_reviews"
    ]
    assert transformed_requirement_schema["required"] == [
        f"gate_{index}" for index in range(8)
    ]
    assert transformed_requirement_schema["additionalProperties"] is False
    assert set(transformed["properties"]) == {
        "requirement_reviews",
        "portfolio_review",
        "prior_finding_reviews",
        "findings",
    }


def test_terminal_schema_requires_complete_judgment_without_arbitrary_caps() -> None:
    material = _material(
        requirements=[_requirement("gate_one"), _requirement("gate_two")]
    )
    schema = architect_metric_semantic_review_json_schema(material)

    assert schema["required"] == [
        "requirement_reviews",
        "portfolio_review",
        "prior_finding_reviews",
        "findings",
    ]
    requirement_schema = schema["properties"]["requirement_reviews"]
    assert requirement_schema["required"] == ["gate_one", "gate_two"]
    assert set(requirement_schema["properties"]) == {"gate_one", "gate_two"}
    assert requirement_schema["additionalProperties"] is False
    assert schema["$defs"]["requirement_review"]["required"] == [
        "status",
        "rationale",
        "evidence_refs",
        "semantic_positive_control",
    ]
    assert schema["$defs"]["requirement_review"]["properties"][
        "semantic_positive_control"
    ]["required"] == ["raw_comparison_value", "rationale", "evidence_refs"]
    assert schema["properties"]["portfolio_review"]["required"] == [
        "status",
        "rationale",
        "evidence_refs",
    ]
    assert "maxItems" not in schema["properties"]["findings"]


def test_metric_reviewer_reports_more_than_eight_distinct_findings() -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]
    findings = []
    for index in range(12):
        finding = _finding()
        finding["summary"] = f"Distinct metric defect {index}."
        finding["observed_behavior"] = f"Observed mismatch {index}."
        findings.append(finding)

    packet, _, _ = _review(
        _payload(requirements, status="FAIL", findings=findings),
        material=material,
    )

    assert packet["overall_verdict"] == "REVISE"
    assert len(packet["findings"]) == 12


def test_finding_evidence_binding_preserves_exact_current_value() -> None:
    material = _material()
    finding = _finding()
    finding["finding_id"] = "finding:one"

    bound = bind_architect_metric_finding_evidence_identities(
        findings=[finding],
        review_material=material,
    )

    binding = bound[0]["evidence_identity_bindings"][0]
    assert binding["evidence_ref"] == "requirement:generic_gate"
    assert binding["artifact_role"] == "metric_protocol_candidate"
    assert binding["semantic_identity_bound"] is True
    assert binding["origin_value_fingerprint"] == stable_hash(
        material["empirical_metric_requirements"][0]
    )


def test_validator_keeps_certificate_and_lineage_fail_closed() -> None:
    material = _material()
    requirements = material["empirical_metric_requirements"]
    packet, _, _ = _review(_payload(requirements), material=material)
    broken = deepcopy(packet)
    broken["runtime_evaluator_certificate_requirement_set_id"] = "other"
    broken["authoring_packet_hash"] = ""

    errors = validate_architect_metric_semantic_review_packet(broken)

    assert "evaluator certificate and reviewed requirement set differ" in errors
    assert "metric review missing trusted lineage field: authoring_packet_hash" in errors


def test_base_schema_stays_generic() -> None:
    requirement_schema = ARCHITECT_METRIC_SEMANTIC_REVIEW_JSON_SCHEMA[
        "properties"
    ]["requirement_reviews"]
    assert requirement_schema == {
        "type": "object",
        "additionalProperties": False,
        "required": [],
        "properties": {},
    }


def _document_material(tmp_path: Path) -> tuple[dict, dict[str, str]]:
    documents = {
        "C1.md": "# C1\n\nSOURCE-LINE:" + "candidate detail " * 3000 + "\n",
        "C1.tex": "Separate exact source.\n",
    }
    for path, content in documents.items():
        (tmp_path / path).write_text(content, encoding="utf-8")
    material = _material()
    semantic = material["theory_developer_protocol_material"]["theory_semantic_material"]
    semantic["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
    semantic["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    semantic["theory_workspace_manifest"] = theory_workspace_document_manifest(
        documents, workspace_dir=tmp_path
    )
    semantic["theory_derivation_packet"] = {
        "claim_index": [{"id": "C1", "document_path": "C1.md", "anchor": "C1"}]
    }
    return material, documents


class _LocalToolBackend:
    provider_name = "local"

    def __init__(self, actions):
        self.actions = iter(actions)
        self.requests = []

    def generate_client_tool_turn(self, request):
        assert request.model == TEST_LOCAL_MODEL
        self.requests.append(request)
        name, payload = next(self.actions)
        payload = payload(request) if callable(payload) else payload
        call = ClientToolCall(f"local-{len(self.requests)}", name, payload)
        return ClientToolTurnResponse(
            content_blocks=({"type": "tool_use", "id": call.call_id,
                             "name": name, "input": payload},),
            tool_calls=(call,), text="", provider="local", model=request.model,
        )


@pytest.mark.parametrize("rejected_call", [
    (THEORY_WORKSPACE_READ_DOCUMENT_TOOL, {"path": "outside.md", "line_start": 1, "line_end": 1}),
    (THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL, {}),
])
def test_metric_roles_receive_one_exact_catalog_and_reviewer_reads_source(tmp_path: Path, rejected_call) -> None:
    material, documents = _document_material(tmp_path)
    theory = material["theory_developer_protocol_material"]
    prompt = build_architect_metric_semantic_review_prompt(
        question=OpenResearchQuestion(id="q_metric_review", title="Generic", description="Review."),
        review_material=material,
    )
    projected, _ = _compact_metric_authoring_prompt_payload(material)
    reviewer_view = json.loads(prompt.split("\n\n", 1)[1])["review_material"]
    author_theory = projected["theory_developer_protocol_material"]["theory_semantic_material"]
    reviewer_theory = reviewer_view["theory_developer_protocol_material"]["theory_semantic_material"]
    assert author_theory == reviewer_theory
    assert author_theory["theory_derivation_packet"]["claim_index"][0]["id"] == "C1"
    catalog = author_theory["authoritative_theory_documents"]
    assert {row["path"] for row in catalog} == set(documents)
    assert catalog[0]["byte_size"] == len(documents["C1.md"].encode())
    assert documents["C1.md"] not in prompt
    assert documents["C1.md"] not in json.dumps(projected)

    backend = _LocalToolBackend([
        rejected_call,
        (THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL, {"query": "# C1", "document_paths": ["C1.md"]}),
        (THEORY_WORKSPACE_READ_DOCUMENT_TOOL, {"path": "C1.md", "line_start": 3, "line_end": 3,
                                             "character_start": 0, "character_end": 24}),
        ("submit_architect_metric_semantic_review", _payload(material["empirical_metric_requirements"])),
    ])
    packet = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="local", model=TEST_LOCAL_MODEL, model_tier="local"
        ),
    ).review(
        question=OpenResearchQuestion(id="q_metric_review", title="Generic", description="Review."),
        review_material=material,
        trusted_lineage={
            "authoring_packet_id": "author:synthetic",
            "authoring_packet_hash": stable_hash({"synthetic": True}),
            "empirical_metric_requirement_set_id": generated_metric_requirement_set_id(material["empirical_metric_requirements"]),
            "source_agent": "MetricProtocolSourceOwner", "source_model": TEST_LOCAL_MODEL,
            "source_model_tier": "local",
            "source_theory_packet_id": theory["source_theory_packet_id"],
            "source_theory_packet_hash": theory["source_theory_packet_hash"],
            "acceptance_authority_catalog_id": material["acceptance_authority_catalog_id"],
            "acceptance_authority_catalog_fingerprint": stable_hash(material["acceptance_authority_catalog"]),
        },
    )
    assert backend.requests[1].messages[-1]["content"][0]["is_error"] is True
    observation = json.loads(backend.requests[3].messages[-1]["content"][0]["content"])
    assert observation["content"] == documents["C1.md"].splitlines()[2][:24]
    inspections = packet["client_tool_loop"]["theory_document_inspection_refs"]
    assert len(inspections) == 2
    assert inspections[-1]["document_sha256"] == catalog[0]["sha256"]
    assert all((tmp_path / path).read_text() == content for path, content in documents.items())


def test_metric_source_owner_reads_the_same_frozen_theory(tmp_path: Path) -> None:
    material, documents = _document_material(tmp_path)
    theory = material["theory_developer_protocol_material"]
    protocol = "# Synthetic protocol\n\nRetain the declared diagnostic before outcomes.\n"

    def review_submission(request):
        prompt_json = request.messages[0]["content"].split("\n\n", 1)[1]
        projected = json.JSONDecoder().raw_decode(prompt_json)[0]["review_material"]
        payload = _payload(projected["empirical_metric_requirements"])
        for row in payload["requirement_reviews"].values():
            row["semantic_positive_control"]["raw_comparison_value"] = True
        return payload

    backend = _LocalToolBackend([
        (THEORY_WORKSPACE_READ_DOCUMENT_TOOL, {"path": "C1.tex", "line_start": 1, "line_end": 1}),
        (METRIC_PROTOCOL_WORKSPACE_READ_TOOL, {}),
        (METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL, {
            "expected_parent_sha256": hashlib.sha256(METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT.encode()).hexdigest(),
            "edits": [{"old_text": METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT, "new_text": protocol}],
        }),
        (METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL, {
            "expected_sha256": hashlib.sha256(protocol.encode()).hexdigest(),
            "required_runtime_replicates": 20, "evaluator_id": "synthetic-evaluator",
            "scientific_rationale": "Synthetic transport fixture, not scientific acceptance.",
        }),
        (THEORY_WORKSPACE_READ_DOCUMENT_TOOL, {"path": "C1.tex", "line_start": 1, "line_end": 1}),
        ("submit_architect_metric_semantic_review", review_submission),
    ])
    preflight = {"packet_id": "preflight:synthetic", "overall_verdict": "ACCEPT"}
    acceptance = {
        "artifact_kind": "RuntimeArchitectTheoryExecutionPreflightAcceptance",
        "execution_results_observed": False, "full_metric_authoring_completed": False,
        "source_theory_packet_id": theory["source_theory_packet_id"],
        "source_theory_packet_hash": theory["source_theory_packet_hash"],
        "theory_execution_preflight_packet": preflight,
        "preflight_packet_id": preflight["packet_id"], "preflight_packet_hash": stable_hash(preflight),
    }
    acceptance["acceptance_id"] = "architect_theory_execution_preflight_acceptance:" + stable_hash(acceptance)[:20]
    reviewer = LLMArchitectMetricSemanticReviewerAgent(
        provider=backend,
        config=ArchitectMetricSemanticReviewerConfig(
            provider_name="local", model=TEST_LOCAL_MODEL, model_tier="local"
        ),
    )
    result = author_reviewed_architect_metric_requirements(
        provider=backend,
        config=ArchitectMetricContractAuthoringConfig(provider_name="local", model_tier="local"),
        request_model=TEST_LOCAL_MODEL, semantic_reviewer=reviewer,
        question=OpenResearchQuestion(id="q_metric_review", title="Synthetic", description="Transport only."),
        theory_protocol_material=theory, accepted_theory_preflight_context=acceptance,
        metric_protocol_workspace_root=tmp_path / "metric",
        runtime_contract={
            "research_evaluation_requires_typed_metric_contracts": True,
            "empirical_metric_requirements": [],
            "empirical_metric_protocol_phase": METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
            "generated_sandbox_runtime_replicates": 20,
        },
    )
    observation = json.loads(backend.requests[1].messages[-1]["content"][0]["content"])
    assert observation["content"] == documents["C1.tex"].rstrip("\n")
    assert result["semantic_review_status"] == "ACCEPT"
    assert len(backend.requests) == 6
    assert result["provider_name"] == "local"
    assert result["semantic_review_packet"]["client_tool_loop"]["theory_document_inspection_refs"][0]["document_sha256"] == observation["document_sha256"]
    assert "read_metric_protocol" not in {tool.name for tool in backend.requests[4].tools}
    assert all((tmp_path / path).read_text() == content for path, content in documents.items())


def test_stale_metric_theory_fails_before_any_local_request(tmp_path: Path) -> None:
    material, _ = _document_material(tmp_path)
    (tmp_path / "C1.md").write_text("Changed after the frozen handoff.\n")
    backend = _LocalToolBackend([])
    with pytest.raises(ValueError, match="document hash mismatch"):
        LLMArchitectMetricSemanticReviewerAgent(
            provider=backend,
            config=ArchitectMetricSemanticReviewerConfig(
                provider_name="local", model=TEST_LOCAL_MODEL, model_tier="local"
            ),
        ).review(
            question=OpenResearchQuestion(id="q_metric_review", title="Generic", description="Review."),
            review_material=material, trusted_lineage={},
        )
    with pytest.raises(ValueError, match="document hash mismatch"):
        _compact_metric_authoring_prompt_payload(material)
    assert backend.requests == []


def test_local_metric_authoring_cannot_silently_skip_independent_review() -> None:
    with pytest.raises(ValueError, match="requires an independent"):
        author_reviewed_architect_metric_requirements(
            provider=_LocalToolBackend([]),
            config=ArchitectMetricContractAuthoringConfig(provider_name="local", model_tier="local"),
            request_model=TEST_LOCAL_MODEL, semantic_reviewer=None,
            question=OpenResearchQuestion(id="q_metric_review", title="Generic", description="Review."),
            runtime_contract={
                "research_evaluation_requires_typed_metric_contracts": True,
                "empirical_metric_requirements": [],
                "empirical_metric_protocol_phase": METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
            },
        )

from __future__ import annotations

from copy import deepcopy
import json

import pytest

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
from ai_statistician.generated_metric_contract import (
    generated_metric_evaluation_semantics_contract,
    generated_metric_requirement_set_id,
)
from ai_statistician.model_backend import ClientToolCall, ClientToolTurnResponse
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.theory_workspace import (
    THEORY_SCRATCHPAD_TOOL,
    TheoryScratchpadConfig,
)


TEST_HAIKU_MODEL = "claude-haiku-4-5-20251001"


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
                    "execution_profile": "scientific_wasm",
                    "dependencies": [],
                    "entrypoint": "run_sandbox",
                    "code": (
                        "def run_sandbox(seed, replicates):\n"
                        "    xs = list(range(10))\n"
                        "    mean = sum(xs) / len(xs)\n"
                        "    value = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)\n"
                        "    return {'sample_variance': value}\n"
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

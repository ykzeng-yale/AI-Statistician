from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ai_statistician.agent_runtime import AgentTask
from ai_statistician.architect_metric_contract_authoring import (
    ArchitectMetricContractAuthoringConfig,
    ArchitectMetricSemanticReviewRejected,
    author_reviewed_architect_metric_requirements,
)
from ai_statistician.architect_theory_execution_preflight import (
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL,
    architect_theory_execution_preflight_json_schema,
    build_architect_theory_execution_preflight_material,
    build_architect_theory_execution_preflight_prompt,
    review_architect_theory_execution_preflight,
    validate_architect_theory_execution_preflight_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.evaluation_protocol_revision import (
    architect_preexecution_metric_protocol_rejection_result,
)
from ai_statistician.metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
)
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolTurnResponse,
    GeneratorResponse,
)
from ai_statistician.research_schema import OpenResearchQuestion


TEST_HAIKU_MODEL = "claude-haiku-4-5-20251001"


class _Backend:
    provider_name = "anthropic"

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return GeneratorResponse(
            text=json.dumps(self.payload),
            provider="anthropic",
            model=request.model,
            metadata={
                "provider_structured_output_requested": True,
                "provider_structured_output_applied": True,
            },
        )


class _SequencedBackend:
    provider_name = "anthropic"

    def __init__(self, initial_payload: dict[str, object]) -> None:
        self.initial_payload = initial_payload
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if len(self.requests) == 1:
            payload = self.initial_payload
        else:
            repair_payload = json.loads(request.user_prompt.split("\n\n", 1)[1])
            path = repair_payload["subsystem_repair_context"][
                "dimension_review_patch_paths"
            ]["primitive_mathematical_consistency"]
            payload = {
                "base_payload_fingerprint": repair_payload[
                    "base_payload_fingerprint"
                ],
                "updates": [
                    {
                        "path": [*path, "evidence_refs"],
                        "replacement_json": json.dumps(
                            ["theory.estimator_specs"]
                        ),
                    }
                ],
            }
        return GeneratorResponse(
            text=json.dumps(payload),
            provider="anthropic",
            model=request.model,
            metadata={
                "provider_structured_output_requested": True,
                "provider_structured_output_applied": True,
            },
        )


def _tool_response(*calls: ClientToolCall) -> ClientToolTurnResponse:
    return ClientToolTurnResponse(
        content_blocks=tuple(
            {
                "type": "tool_use",
                "id": call.call_id,
                "name": call.name,
                "input": dict(call.input),
            }
            for call in calls
        ),
        tool_calls=tuple(calls),
        text="",
        provider="anthropic",
        model=TEST_HAIKU_MODEL,
        metadata={
            "client_tool_transport": True,
            "tools_executed_by_backend": False,
            "provider_stop_reason": "tool_use",
            "provider_usage": {"input_tokens": 19, "output_tokens": 7},
        },
    )


class _PreflightToolBackend:
    provider_name = "anthropic"

    def __init__(
        self,
        *,
        accept: bool,
        payload: dict[str, object] | None = None,
        submit_before_search: bool = False,
        submit_unknown_ref_once: bool = False,
        source_scope: str = "theory",
    ) -> None:
        self.accept = accept
        self.payload = deepcopy(payload) if payload is not None else None
        self.submit_before_search = submit_before_search
        self.submit_unknown_ref_once = submit_unknown_ref_once
        self.source_scope = source_scope
        self.requests = []
        self.hit_id = ""
        self.source_ref = ""

    def _submission(self, *, source_ref: str) -> dict[str, object]:
        payload = deepcopy(self.payload) if self.payload is not None else _payload(
            accept=self.accept
        )
        for finding in payload["findings"]:
            finding["source_evidence_refs"] = [source_ref]
        for review in payload.get("prior_finding_reviews", []) or []:
            current_finding = review.get("current_finding")
            if isinstance(current_finding, dict):
                current_finding["source_evidence_refs"] = [source_ref]
        return payload

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        turn = len(self.requests)
        if turn == 1 and self.submit_before_search:
            return _tool_response(
                ClientToolCall(
                    "submit-too-early",
                    "submit_theory_preflight_review",
                    self._submission(source_ref="not-yet-observed"),
                )
            )
        if turn == 1 or (turn == 2 and self.submit_before_search):
            return _tool_response(
                ClientToolCall(
                    "search-1",
                    "search_preflight_sources",
                    {
                        "query": "finite input censored outcome",
                        "source_scope": self.source_scope,
                        "k": 4,
                    },
                )
            )
        result_blocks = request.messages[-1]["content"]
        result = json.loads(result_blocks[0]["content"])
        if result.get("hits"):
            self.hit_id = result["hits"][0]["source_hit_id"]
            self.source_ref = result["hits"][0]["source_ref"]
        if self.submit_unknown_ref_once and not any(
            row.get("is_error")
            for row in request.messages[-1].get("content", [])
            if isinstance(row, dict)
        ):
            self.submit_unknown_ref_once = False
            return _tool_response(
                ClientToolCall(
                    "submit-unknown-ref",
                    "submit_theory_preflight_review",
                    self._submission(source_ref="S99H99"),
                )
            )
        return _tool_response(
            ClientToolCall(
                f"submit-{turn}",
                "submit_theory_preflight_review",
                self._submission(source_ref=self.source_ref),
            )
        )


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="generic_resource_bounded_procedure",
        title="Review an ideal procedure and its finite observation",
        description=(
            "Develop and evaluate a statistical procedure whose ideal definition "
            "may consume a data stream of unspecified length."
        ),
    )


def _theory_material() -> dict[str, object]:
    semantic_material = {
        "problem_card": {
            "observed_data": "A stream of observations from a declared sampling law.",
            "dgp": "Independent observations under two declared parameter regimes.",
            "estimand": "A risk and a resource-use functional of the ideal procedure.",
            "assumptions": ["The ideal procedure is adapted to observed data."],
        },
        "estimator_specs": [
            {
                "id": "generic_stream_method",
                "formula": "T = first index at which a declared event occurs",
                "algorithm": "Read observations until the event occurs and return T.",
                "inputs": ["a finite serialized observation array"],
                "outputs": ["T"],
                "sample_size_order": "The ideal procedure has unspecified duration.",
                "estimator_interface_contract": {
                    "request_fields": [
                        {"name": "observations", "binding": "per_replicate_data"}
                    ],
                    "response_fields": [
                        {
                            "name": "T",
                            "meaning": "ideal first-event index",
                            "normalization": "positive integer or typed censored outcome",
                            "sample_size_order": "bounded by the serialized input length",
                        }
                    ],
                },
            }
        ],
        "simulation_ademp_spec": {
            "dgps": ["Generate a fixed finite number of observations."],
            "methods": ["Apply the ideal procedure."],
            "performance_measures": ["Mean ideal resource use."],
        },
        "theory_derivation_packet": {
            "derivation_steps": [
                {
                    "id": "claim_1",
                    "claim": "The ideal procedure always returns.",
                    "equation_or_argument": "The event is expected to occur eventually.",
                }
            ],
            "equation_chain": [
                {
                    "step_id": "E1",
                    "lhs": "E[T]",
                    "rhs": "a finite quantity",
                    "justification": "asserted from the event definition",
                }
            ],
            "assumption_ledger": [
                {"assumption": "eventual occurrence", "used_in": ["claim_1"]}
            ],
            "sanity_checks": [],
            "self_critique": [
                {
                    "finding": "The finite input may end before the event.",
                    "resolution": "Expose that case as a typed censored outcome.",
                }
            ],
            "rejected_alternatives": [
                {
                    "candidate": "Pretend every finite input contains the event.",
                    "reason": "That changes the declared observation law.",
                }
            ],
        },
        "theorem_cards": [
            {"id": "theorem_1", "conclusion": "The ideal risk is controlled."}
        ],
        "lemma_cards": [],
        "critic_findings": [
            {
                "id": "resolved_finite_input_risk",
                "finding": "A finite input may omit the ideal event.",
                "resolution": "The accepted fixture declares a typed censored output.",
            }
        ],
    }
    return {
        "artifact_kind": "RuntimeTheoryInformedMetricProtocolMaterial",
        "source_theory_packet_id": "theory_derivation:generic",
        "source_theory_packet_hash": stable_hash(semantic_material),
        "theory_semantic_material": semantic_material,
        "execution_results_available": False,
    }


def _payload(*, accept: bool) -> dict[str, object]:
    status = "PASS" if accept else "FAIL"
    return {
        "dimension_reviews": [
            {
                "status": status,
                "rationale": (
                    "The primitive claim and finite observation agree."
                    if accept
                    else "The ideal object and finite observation are not aligned."
                ),
                "evidence_refs": [
                    "theory.problem_card",
                    "theory.estimator_specs",
                ],
            }
            for _dimension in ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
        ],
        "estimator_execution_checks": [
            {
                "audit_rationale": (
                    "The first-event identity is reconstructed on event and no-event "
                    "finite-support branches; the adapted stopping rule, theorem use, "
                    "typed finite outcome, and guarantee transport all match the source."
                    if accept
                    else "The source merely asserts eventual occurrence and does not "
                    "connect the stopped finite observation to the claimed ideal risk."
                ),
                "procedure_identity_declared_valid": accept,
                "theorem_applications_declared_valid": accept,
                "ideal_to_executable_mapping_declared": accept,
                "total_or_typed_bounded_outcome_declared": accept,
                "guarantee_transport_argument_declared": accept,
                "boundary_or_counterexample": (
                    "The no-event finite input returns the censored outcome."
                    if accept
                    else "A finite input with no event makes the declared method undefined."
                ),
                "status": status,
                "evidence_refs": [
                    "theory.estimator_specs",
                    "theory.simulation_ademp_spec",
                ],
            }
        ],
        "findings": (
            []
            if accept
            else [
                {
                    "severity": "high",
                    "category": "ideal_executable_semantic_mismatch",
                    "summary": "The finite interface does not represent all ideal outcomes.",
                    "required_change": (
                        "Define a total executable outcome and the estimand induced by "
                        "any resource bound or censoring rule."
                    ),
                    "evidence_refs": [
                        "theory.estimator_specs",
                        "theory.simulation_ademp_spec",
                    ],
                }
            ]
        ),
    }


def _review(*, accept: bool):
    backend = _Backend(_payload(accept=accept))
    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=0,
    )
    return packet, backend


def _tool_review(backend, *, source_retriever=None, prior_finding_ledger=()):
    return review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=0,
        source_retriever=source_retriever,
        prior_finding_ledger=prior_finding_ledger,
    )


def test_preflight_client_tool_loop_searches_before_grounded_submission() -> None:
    backend = _PreflightToolBackend(accept=False)

    packet = _tool_review(backend)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["source_grounding_required"] is True
    assert packet["source_grounding_transport"] == "client_tool_source_query_v3"
    assert packet["preflight_source_search_count"] == 1
    assert packet["client_tool_loop_turns"] == 2
    assert packet["client_tool_loop_tool_calls"] == 2
    assert packet["client_tool_loop_runtime_executed_tool_calls"] == 2
    assert packet["runtime_selected_review_semantics"] is False
    assert packet["findings"][0]["source_evidence_refs"] == [backend.hit_id]
    assert packet["source_grounding_bindings"] == [
        {
            "finding_id": packet["findings"][0]["finding_id"],
            "source_evidence_refs": [backend.hit_id],
            "runtime_verified_source_refs": True,
            "runtime_selected_semantics": False,
        }
    ]
    assert backend.requests[0].model == TEST_HAIKU_MODEL
    assert [tool.name for tool in backend.requests[0].tools] == [
        "search_preflight_sources",
        "submit_theory_preflight_review",
    ]
    assert backend.requests[0].metadata["model_tier"] == "haiku"
    assert backend.requests[0].disable_parallel_tool_use is True
    first_result = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert first_result["hits"][0]["source_ref"] == "S1H1"


def test_preflight_canonicalizes_prior_finding_source_ref_before_binding() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_id = rejected["active_unresolved_finding_ids"][0]
    payload = _payload(accept=False)
    continuation = payload["findings"].pop()
    payload["prior_finding_reviews"] = [
        {
            "status": "UNRESOLVED",
            "rationale": "The revised source still leaves the finite branch undefined.",
            "evidence_refs": ["theory.estimator_specs"],
            "current_finding": continuation,
        }
    ]
    backend = _PreflightToolBackend(accept=False, payload=payload)

    packet = _tool_review(backend, prior_finding_ledger=prior_ledger)

    continued = packet["findings"][0]
    assert continued["finding_id"] == prior_finding_id
    assert continued["source_evidence_refs"] == [backend.hit_id]
    assert packet["runtime_prior_finding_identity_bindings"][0][
        "model_continuation_fingerprint"
    ] == stable_hash(
        {
            key: value
            for key, value in continued.items()
            if key not in {"finding_id", "prior_finding_id", "repair_scope"}
        }
    )


def test_preflight_client_tool_loop_can_query_configured_formal_retriever() -> None:
    class FormalRetriever:
        source = "configured_formal_source"

        def __init__(self) -> None:
            self.queries = []

        def search(self, query, *, k):
            self.queries.append((query, k))
            return [
                {
                    "source_id": "statlib",
                    "path": "Statlib/Survival.lean",
                    "line": 17,
                    "kind": "theorem",
                    "name": "Statlib.example",
                    "signature": "example_statement",
                    "score": 2.5,
                }
            ]

    retriever = FormalRetriever()
    backend = _PreflightToolBackend(
        accept=False,
        source_scope="formal_library",
    )

    packet = _tool_review(backend, source_retriever=retriever)

    assert retriever.queries == [("finite input censored outcome", 4)]
    hit = packet["preflight_source_observations"][0]["hits"][0]
    assert hit["source_kind"] == "formal_library_declaration"
    assert hit["source_identity"].startswith("statlib:")
    assert packet["findings"][0]["source_evidence_refs"] == [
        hit["source_hit_id"]
    ]


def test_preflight_all_scope_preserves_context_and_formal_channels() -> None:
    class FormalRetriever:
        source = "configured_formal_source"

        def search(self, query, *, k):
            return [
                {
                    "source_id": "statlib",
                    "path": "Statlib/Generic.lean",
                    "line": 17,
                    "kind": "theorem",
                    "name": "Statlib.generic",
                    "signature": "finite input censored outcome",
                    "score": 9999.0,
                }
            ]

    backend = _PreflightToolBackend(
        accept=False,
        source_scope="all",
    )

    packet = _tool_review(backend, source_retriever=FormalRetriever())

    hits = packet["preflight_source_observations"][0]["hits"]
    assert {hit["retrieval_channel"] for hit in hits} == {
        "theory_and_retrieval_context",
        "formal_library",
    }
    assert hits[0]["retrieval_channel"] == "theory_and_retrieval_context"
    assert [hit["source_ref"] for hit in hits] == [
        f"S1H{index + 1}" for index in range(len(hits))
    ]
    assert packet["findings"][0]["source_evidence_refs"] == [
        hits[0]["source_hit_id"]
    ]


def test_preflight_source_search_deduplicates_hits_across_turns() -> None:
    class RepeatedSearchBackend(_PreflightToolBackend):
        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn <= 2:
                if turn == 2:
                    first_result = json.loads(
                        request.messages[-1]["content"][0]["content"]
                    )
                    self.source_ref = first_result["hits"][0]["source_ref"]
                    self.hit_id = first_result["hits"][0]["source_hit_id"]
                return _tool_response(
                    ClientToolCall(
                        f"search-{turn}",
                        "search_preflight_sources",
                        {
                            "query": "finite input censored outcome",
                            "source_scope": "theory",
                            "k": 4,
                        },
                    )
                )
            return _tool_response(
                ClientToolCall(
                    "submit-after-repeat",
                    "submit_theory_preflight_review",
                    self._submission(source_ref=self.source_ref),
                )
            )

    packet = _tool_review(RepeatedSearchBackend(accept=False))

    first, second = packet["preflight_source_observations"]
    first_ids = {row["source_hit_id"] for row in first["hits"]}
    second_ids = {row["source_hit_id"] for row in second["hits"]}
    assert first_ids.isdisjoint(second_ids)
    assert set(second["duplicate_source_refs_reused"]).issubset(
        {row["source_ref"] for row in first["hits"]}
    )
    assert second["duplicate_source_refs_reused"]


def test_preflight_client_tool_loop_returns_unknown_ref_error_for_model_repair() -> None:
    backend = _PreflightToolBackend(
        accept=False,
        submit_unknown_ref_once=True,
    )

    packet = _tool_review(backend)

    assert len(backend.requests) == 3
    assert packet["findings"][0]["source_evidence_refs"] == [backend.hit_id]
    failed_submit = packet["client_tool_loop_history"][1]["tool_calls"][0]
    assert failed_submit["name"] == "submit_theory_preflight_review"
    assert failed_submit["is_error"] is True
    assert "runtime-returned source refs" in failed_submit["result_excerpt"]
    assert "available handles: S1H1" in failed_submit["result_excerpt"]


def test_preflight_recovers_from_rejected_final_submission() -> None:
    class FinalSubmissionRecoveryBackend(_PreflightToolBackend):
        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn > 1:
                result_blocks = request.messages[-1]["content"]
                for block in result_blocks:
                    result = json.loads(block["content"])
                    if result.get("hits"):
                        self.hit_id = result["hits"][0]["source_hit_id"]
                        self.source_ref = result["hits"][0]["source_ref"]
            if turn <= 3:
                return _tool_response(
                    ClientToolCall(
                        f"search-{turn}",
                        "search_preflight_sources",
                        {
                            "query": "finite input censored outcome",
                            "source_scope": "theory",
                            "k": 4,
                        },
                    )
                )
            source_ref = (
                "S99H99" if turn == 4 else self.source_ref
            )
            return _tool_response(
                ClientToolCall(
                    f"submit-{turn}",
                    "submit_theory_preflight_review",
                    self._submission(source_ref=source_ref),
                )
            )

    backend = FinalSubmissionRecoveryBackend(accept=False)

    packet = _tool_review(backend)

    assert len(backend.requests) == 5
    assert [tool.name for tool in backend.requests[3].tools] == [
        "submit_theory_preflight_review"
    ]
    assert [tool.name for tool in backend.requests[4].tools] == [
        "submit_theory_preflight_review"
    ]
    assert backend.requests[4].metadata[
        "client_tool_loop_max_terminal_recovery_turns"
    ] == 1
    failed_submit = packet["client_tool_loop_history"][3]["tool_calls"][0]
    assert failed_submit["is_error"] is True
    assert packet["client_tool_loop_turns"] == 5


def test_preflight_client_tool_loop_rejects_submit_before_search() -> None:
    backend = _PreflightToolBackend(
        accept=False,
        submit_before_search=True,
    )

    packet = _tool_review(backend)

    assert len(backend.requests) == 3
    first_submit = packet["client_tool_loop_history"][0]["tool_calls"][0]
    assert first_submit["is_error"] is True
    assert "must run before submission" in first_submit["result_excerpt"]
    assert packet["preflight_source_search_count"] == 1


def test_preflight_client_tool_loop_failure_is_fail_closed() -> None:
    class NoToolBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            return _tool_response()

    backend = NoToolBackend()

    with pytest.raises(PacketValidationError) as exc_info:
        _tool_review(backend)

    assert len(backend.requests) == 3
    assert "repeated turns without a client tool call" in str(exc_info.value)


def test_preflight_static_transport_is_explicitly_ungrounded() -> None:
    packet, _backend = _review(accept=True)

    assert packet["source_grounding_required"] is False
    assert packet["source_grounding_transport"] == (
        "legacy_structured_output_without_client_tools"
    )
    assert packet["source_grounding_bindings"] == []


def test_preflight_is_compact_generic_and_haiku_pinned() -> None:
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    prompt = build_architect_theory_execution_preflight_prompt(material)
    prompt_payload = json.loads(prompt.split("\n\n", 1)[1])
    packet, backend = _review(accept=True)

    assert len(prompt) < 30_000
    protocol = " ".join(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL)
    for phrase in (
        "full declared support",
        "recompute the procedure-defining identity",
        "condition on the information available",
        "fixed-candidate result does not automatically survive",
        "source_interface_inventory",
        "present-but-incomplete contract",
        "do not substitute a hypothetical branch",
        "same DGP, probability law",
        "finite executable observation",
        "typed outcome",
        "not observed within a resource bound",
        "neither automatically destroys nor automatically preserves",
    ):
        assert phrase in protocol
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["runtime_estimator_status_normalizations"] == []
    assert packet["runtime_estimator_identity_bindings"][0][
        "identity_source"
    ] == "estimator_execution_checks_ordered_index"
    assert packet["runtime_estimator_identity_bindings"][0][
        "runtime_selected_semantics"
    ] is False
    assert packet["execution_authorized"] is False
    assert packet["kernel_verified"] is False
    assert packet["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")
    anchor_ids = {
        row["anchor_id"] for row in material["anchor_catalog"]
    }
    assert {
        "theory.self_critique",
        "theory.rejected_alternatives",
        "theory.critic_findings",
    } <= anchor_ids
    estimator_anchor = next(
        row
        for row in material["anchor_catalog"]
        if row["anchor_id"] == "theory.estimator_specs"
    )
    assert estimator_anchor["content"][0]["source_interface_inventory"] == {
        "declared_outputs": [{"name": "T"}],
        "request_fields": [
            {"name": "observations", "binding": "per_replicate_data"}
        ],
        "response_fields": [
            {
                "name": "T",
                "meaning": "ideal first-event index",
                "normalization": "positive integer or typed censored outcome",
                "sample_size_order": "bounded by the serialized input length",
            }
        ],
    }
    assert backend.requests[0].model == TEST_HAIKU_MODEL
    assert backend.requests[0].metadata["model_tier"] == "haiku"
    assert backend.requests[0].max_tokens == 5600
    assert backend.requests[0].metadata["review_output_token_cap"] == 5600
    assert "not theorem peer review" in backend.requests[0].system_prompt
    assert "Exclude downstream proof obligations" in (
        backend.requests[0].schema["properties"]["findings"]["description"]
    )
    dimension_schema = backend.requests[0].schema["properties"][
        "dimension_reviews"
    ]
    assert dimension_schema["type"] == "array"
    assert dimension_schema["minItems"] == len(
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS
    )
    estimator_schema = backend.requests[0].schema["properties"][
        "estimator_execution_checks"
    ]
    assert estimator_schema["items"] == {
        "$ref": "#/$defs/estimator_execution_check"
    }
    assert "estimator_id" not in backend.requests[0].schema["$defs"][
        "estimator_execution_check"
    ]["properties"]
    assert "repair_instructions" not in backend.requests[0].schema["properties"]
    assert prompt_payload["ordered_review_slots"][
        "estimator_execution_checks"
    ] == [{"output_index": 0, "estimator_id": "generic_stream_method"}]
    assert "prior_finding_reviews" not in backend.requests[0].schema[
        "properties"
    ]
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_patch_paths_follow_raw_ordered_index_transport() -> None:
    initial_payload = _payload(accept=False)
    primitive_index = ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS.index(
        "primitive_mathematical_consistency"
    )
    initial_payload["dimension_reviews"][primitive_index]["evidence_refs"] = [
        "unknown.anchor"
    ]
    backend = _SequencedBackend(initial_payload)

    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=1,
    )

    repair_payload = json.loads(backend.requests[1].user_prompt.split("\n\n", 1)[1])
    context = repair_payload["subsystem_repair_context"]
    assert "current_invalid_packet" not in context
    assert context["dimension_review_patch_paths"][
        "primitive_mathematical_consistency"
    ] == ["dimension_reviews", primitive_index]
    assert context["estimator_execution_check_patch_paths"] == [
        {
            "estimator_id": "generic_stream_method",
            "path": ["estimator_execution_checks", 0],
        }
    ]
    assert packet["overall_verdict"] == "REVISE"
    assert packet["llm_json_repair_history"][1]["patched_paths"] == [
        [
            "dimension_reviews",
            primitive_index,
            "evidence_refs",
        ]
    ]


def test_preflight_prior_finding_schema_does_not_expand_per_finding() -> None:
    base_material = {
        "anchor_catalog": [
            {"anchor_id": "theory.estimator_specs"},
            {"anchor_id": "theory.theorem_cards"},
        ],
        "required_estimator_ids": ["generic_stream_method"],
    }
    one_schema = architect_theory_execution_preflight_json_schema(
        {**base_material, "active_prior_finding_ids": ["finding:0"]}
    )
    six_schema = architect_theory_execution_preflight_json_schema(
        {
            **base_material,
            "active_prior_finding_ids": [
                f"finding:{index}" for index in range(6)
            ],
        }
    )

    prior_schema = six_schema["properties"]["prior_finding_reviews"]
    assert prior_schema["type"] == "array"
    assert prior_schema["minItems"] == 6
    assert prior_schema["maxItems"] == 6
    assert prior_schema["items"] == {
        "$ref": "#/$defs/prior_finding_review"
    }
    assert len(json.dumps(six_schema, separators=(",", ":"))) == len(
        json.dumps(one_schema, separators=(",", ":"))
    )


def test_preflight_estimator_transport_is_compact_and_semantically_owned() -> None:
    schema = architect_theory_execution_preflight_json_schema(
        {
            "anchor_catalog": [{"anchor_id": "theory.estimator_specs"}],
            "required_estimator_ids": ["estimator_0", "estimator_1"],
            "active_prior_finding_ids": [],
        }
    )
    estimator_schema = schema["$defs"]["estimator_execution_check"]

    assert estimator_schema["required"] == [
        "audit_rationale",
        "procedure_identity_declared_valid",
        "theorem_applications_declared_valid",
        "ideal_to_executable_mapping_declared",
        "total_or_typed_bounded_outcome_declared",
        "guarantee_transport_argument_declared",
        "boundary_or_counterexample",
        "status",
        "evidence_refs",
    ]
    assert set(estimator_schema["properties"]) == set(
        estimator_schema["required"]
    )
    assert estimator_schema["properties"]["audit_rationale"]["maxLength"] == 720


def test_preflight_cannot_accept_an_unestablished_procedure_identity() -> None:
    packet, _backend = _review(accept=True)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    packet["estimator_execution_checks"][0][
        "procedure_identity_declared_valid"
    ] = False

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )

    assert any("established procedure identity" in error for error in errors)
    assert any(
        "estimator_execution_checks[0].procedure_identity_declared_valid"
        in error
        and "estimator_id='generic_stream_method'" in error
        for error in errors
    )
    assert any(
        "consistency warnings mismatch" in error
        for error in errors
    )
    assert any("overall verdict is not runtime-derived" in error for error in errors)


def test_preflight_cannot_accept_invalid_theorem_application() -> None:
    packet, _backend = _review(accept=True)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    packet["estimator_execution_checks"][0][
        "theorem_applications_declared_valid"
    ] = False

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )

    assert any("valid theorem applications" in error for error in errors)
    assert any(
        "estimator_execution_checks[0].theorem_applications_declared_valid"
        in error
        and "estimator_id='generic_stream_method'" in error
        for error in errors
    )
    assert any("consistency warnings mismatch" in error for error in errors)


def test_preflight_preserves_primitive_summary_conflict_without_retry() -> None:
    payload = _payload(accept=False)
    payload["dimension_reviews"][1] = {
        "status": "PASS",
        "rationale": "The primitive formulas are internally well formed.",
        "evidence_refs": ["theory.estimator_specs"],
    }
    backend = _Backend(payload)

    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=1,
    )
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )

    assert len(backend.requests) == 1
    assert packet["overall_verdict"] == "REVISE"
    assert packet["derived_consistency_warnings"][0]["warning_code"] == (
        "primitive_summary_conflicts_with_estimator_checks"
    )
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_downgrades_inconsistent_estimator_pass_without_retry() -> None:
    payload = _payload(accept=True)
    payload["dimension_reviews"][1] = {
        "status": "UNCERTAIN",
        "rationale": "One invoked theorem hypothesis is not established.",
        "evidence_refs": ["theory.theorem_cards", "theory.estimator_specs"],
    }
    payload["estimator_execution_checks"][0][
        "theorem_applications_declared_valid"
    ] = False
    payload["estimator_execution_checks"][0][
        "audit_rationale"
    ] = "The source does not establish every invoked theorem hypothesis."
    payload["findings"] = [
        {
            "severity": "high",
            "category": "unestablished_theorem_hypothesis",
            "summary": "An invoked theorem hypothesis remains unestablished.",
            "required_change": (
                "Establish the hypothesis under the law used by the conclusion."
            ),
            "evidence_refs": ["theory.theorem_cards", "theory.estimator_specs"],
        }
    ]
    backend = _Backend(payload)

    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=1,
    )
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )

    assert len(backend.requests) == 1
    estimator_row = packet["estimator_execution_checks"][0]
    assert estimator_row["status"] == "UNCERTAIN"
    assert estimator_row["theorem_applications_declared_valid"] is False
    assert packet["overall_verdict"] == "REVISE"
    assert packet["findings"][0]["category"] == (
        "unestablished_theorem_hypothesis"
    )
    assert packet["repair_instructions"] == [
        packet["findings"][0]["required_change"]
    ]
    assert packet["runtime_estimator_status_normalizations"] == [
        {
            "estimator_id": "generic_stream_method",
            "model_reported_status": "PASS",
            "runtime_normalized_status": "UNCERTAIN",
            "false_or_missing_declaration_fields": [
                "theorem_applications_declared_valid"
            ],
            "rule": (
                "A PASS estimator summary requires every granular declaration flag "
                "to be true; the runtime only downgraded the redundant summary and "
                "preserved all model-authored semantic fields."
            ),
            "runtime_selected_semantics": False,
        }
    ]
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_routes_semantic_mismatch_to_upstream_theory() -> None:
    packet, _backend = _review(accept=False)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["findings"][0]["repair_scope"] == "upstream_theory"
    assert packet["generated_code_observed"] is False
    assert packet["simulation_results_observed"] is False


def test_preflight_closes_prior_findings_by_stable_identity() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_ids = rejected["active_unresolved_finding_ids"]
    assert len(prior_finding_ids) == 1
    assert rejected["findings"][0]["finding_id"] == prior_finding_ids[0]

    accepted_payload = _payload(accept=True)
    accepted_payload["prior_finding_reviews"] = [
        {
            "status": "RESOLVED_BY_CURRENT_THEORY",
            "rationale": (
                "The current estimator interface now exposes the bounded outcome."
            ),
            "evidence_refs": ["theory.estimator_specs"],
            "current_finding": None,
        }
    ]
    backend = _Backend(accepted_payload)
    accepted = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=0,
        prior_finding_ledger=prior_ledger,
    )

    prior_review_schema = backend.requests[0].schema["properties"][
        "prior_finding_reviews"
    ]
    assert prior_review_schema["type"] == "array"
    assert prior_review_schema["minItems"] == 1
    assert prior_review_schema["maxItems"] == 1
    assert prior_review_schema["items"] == {
        "$ref": "#/$defs/prior_finding_review"
    }
    prior_review_definition = backend.requests[0].schema["$defs"][
        "prior_finding_review"
    ]
    assert "finding_id" not in prior_review_definition["properties"]
    assert "current_finding" in prior_review_definition["required"]
    assert prior_review_definition["properties"]["current_finding"]["anyOf"][
        1
    ] == {"type": "null"}
    finding_definition = backend.requests[0].schema["$defs"]["finding"]
    assert "prior_finding_id" not in finding_definition["properties"]
    assert accepted["overall_verdict"] == "ACCEPT"
    assert accepted["active_unresolved_finding_ids"] == []
    assert accepted["runtime_prior_finding_identity_bindings"] == []
    assert accepted["prior_finding_resolution_summary"] == {
        "prior_active_finding_ids": prior_finding_ids,
        "resolved_prior_finding_ids": prior_finding_ids,
        "still_unresolved_prior_finding_ids": [],
        "new_finding_ids": [],
        "progress_made": True,
        "stalled": False,
    }
    assert accepted["cumulative_finding_ledger"][0]["status"] == (
        "RESOLVED_BY_CURRENT_THEORY"
    )


def test_preflight_binds_unresolved_prior_finding_from_ordered_index() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_id = rejected["active_unresolved_finding_ids"][0]
    initial_payload = _payload(accept=False)
    continuation = initial_payload["findings"].pop()
    continuation["summary"] = (
        "The revised finite interface still omits one declared outcome."
    )
    initial_payload["findings"] = [
        {
            "severity": "medium",
            "category": "new_finite_branch_gap",
            "summary": "A separate finite branch also needs an explicit outcome.",
            "required_change": "Declare the finite outcome for that branch.",
            "evidence_refs": ["theory.estimator_specs"],
        }
    ]
    initial_payload["prior_finding_reviews"] = [
        {
            "status": "UNRESOLVED",
            "rationale": "The revised source still leaves the finite branch undefined.",
            "evidence_refs": ["theory.estimator_specs"],
            "current_finding": continuation,
        }
    ]
    backend = _Backend(initial_payload)
    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=0,
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 1
    finding_schema = backend.requests[0].schema["$defs"]["finding"]
    assert "prior_finding_id" not in finding_schema["properties"]
    assert "finding_id" not in finding_schema["properties"]
    prior_schema = backend.requests[0].schema["properties"][
        "prior_finding_reviews"
    ]["items"]
    assert prior_schema == {"$ref": "#/$defs/prior_finding_review"}
    assert "current_finding" in backend.requests[0].schema["$defs"][
        "prior_finding_review"
    ]["required"]
    assert packet["findings"][0]["prior_finding_id"] == prior_finding_id
    assert packet["findings"][0]["finding_id"] == prior_finding_id
    assert packet["findings"][0]["summary"] == continuation["summary"]
    assert packet["findings"][1].get("prior_finding_id", "") == ""
    assert packet["runtime_prior_finding_identity_bindings"] == [
        {
            "transport_index": 0,
            "prior_finding_id": prior_finding_id,
            "canonical_finding_id": prior_finding_id,
            "model_continuation_fingerprint": stable_hash(continuation),
            "identity_source": "prior_finding_reviews_ordered_index",
            "runtime_selected_semantics": False,
        }
    ]
    assert packet["prior_finding_resolution_summary"][
        "still_unresolved_prior_finding_ids"
    ] == [prior_finding_id]
    assert packet["prior_finding_resolution_summary"]["new_finding_ids"] == [
        packet["findings"][1]["finding_id"]
    ]
    assert packet["prior_finding_resolution_summary"]["progress_made"] is False
    assert packet["prior_finding_resolution_summary"]["stalled"] is True
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=build_architect_theory_execution_preflight_material(
            question=_question(),
            theory_protocol_material=_theory_material(),
            upstream_research_contract={
                "formal_targets": [],
                "simulation_targets": ["evaluate the declared risk"],
            },
            prior_finding_ledger=prior_ledger,
        ),
    ) == []


def test_preflight_repairs_missing_ordered_prior_continuation() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_id = rejected["active_unresolved_finding_ids"][0]
    initial_payload = _payload(accept=False)
    continuation = initial_payload["findings"].pop()
    initial_payload["prior_finding_reviews"] = [
        {
            "status": "UNRESOLVED",
            "rationale": "The finite source branch remains undefined.",
            "evidence_refs": ["theory.estimator_specs"],
            "current_finding": None,
        }
    ]

    class MissingContinuationBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.repair_context = {}

        def generate(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = initial_payload
            else:
                repair_payload = json.loads(request.user_prompt.split("\n\n", 1)[1])
                self.repair_context = repair_payload["subsystem_repair_context"]
                prior_row = self.repair_context[
                    "prior_finding_review_patch_paths"
                ][0]
                payload = {
                    "base_payload_fingerprint": repair_payload[
                        "base_payload_fingerprint"
                    ],
                    "updates": [
                        {
                            "path": prior_row["current_finding_path"],
                            "replacement_json": json.dumps(continuation),
                        }
                    ],
                }
            return GeneratorResponse(
                text=json.dumps(payload),
                provider="anthropic",
                model=request.model,
                metadata={
                    "provider_structured_output_requested": True,
                    "provider_structured_output_applied": True,
                },
            )

    backend = MissingContinuationBackend()
    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=1,
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 2
    assert backend.repair_context["current_finding_patch_paths"] == []
    assert backend.repair_context["prior_finding_review_patch_paths"] == [
        {
            "finding_id": prior_finding_id,
            "path": ["prior_finding_reviews", 0],
            "current_finding_path": [
                "prior_finding_reviews",
                0,
                "current_finding",
            ],
        }
    ]
    assert packet["findings"][0]["prior_finding_id"] == prior_finding_id
    assert packet["findings"][0]["finding_id"] == prior_finding_id
    assert packet["runtime_prior_finding_identity_bindings"][0][
        "runtime_selected_semantics"
    ] is False
    assert packet["llm_json_repair_attempts"] == 1


def test_preflight_repairs_missing_ordered_prior_row_by_replacing_array() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    second_prior = deepcopy(prior_ledger[0])
    second_prior["finding_id"] = "metric_protocol_finding:second"
    second_prior["finding"] = {
        **second_prior["finding"],
        "finding_id": second_prior["finding_id"],
        "summary": "A second declared executable outcome remains unspecified.",
    }
    prior_ledger = [*prior_ledger, second_prior]
    prior_finding_ids = [row["finding_id"] for row in prior_ledger]
    resolved_rows = [
        {
            "status": "RESOLVED_BY_CURRENT_THEORY",
            "rationale": "The current theory now declares this executable outcome.",
            "evidence_refs": ["theory.estimator_specs"],
            "current_finding": None,
        }
        for _finding_id in prior_finding_ids
    ]
    initial_payload = _payload(accept=True)
    initial_payload["prior_finding_reviews"] = resolved_rows[:1]

    class MissingPriorRowBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.repair_context = {}

        def generate(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = initial_payload
            else:
                repair_payload = json.loads(request.user_prompt.split("\n\n", 1)[1])
                self.repair_context = repair_payload["subsystem_repair_context"]
                payload = {
                    "base_payload_fingerprint": repair_payload[
                        "base_payload_fingerprint"
                    ],
                    "updates": [
                        {
                            "path": self.repair_context[
                                "prior_finding_reviews_array_path"
                            ],
                            "replacement_json": json.dumps(resolved_rows),
                        }
                    ],
                }
            return GeneratorResponse(
                text=json.dumps(payload),
                provider="anthropic",
                model=request.model,
                metadata={
                    "provider_structured_output_requested": True,
                    "provider_structured_output_applied": True,
                },
            )

    backend = MissingPriorRowBackend()
    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        max_repair_attempts=1,
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 2
    assert backend.repair_context["prior_finding_review_patch_paths"] == [
        {
            "finding_id": prior_finding_ids[0],
            "path": ["prior_finding_reviews", 0],
            "current_finding_path": [
                "prior_finding_reviews",
                0,
                "current_finding",
            ],
        }
    ]
    assert backend.repair_context["prior_finding_reviews_array_path"] == [
        "prior_finding_reviews"
    ]
    assert backend.repair_context["prior_finding_review_transport_slots"] == [
        {
            "output_index": 0,
            "finding_id": prior_finding_ids[0],
            "base_row_exists": True,
        },
        {
            "output_index": 1,
            "finding_id": prior_finding_ids[1],
            "base_row_exists": False,
        },
    ]
    assert [
        row["finding_id"] for row in packet["prior_finding_reviews"]
    ] == prior_finding_ids
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["llm_json_repair_attempts"] == 1


def test_rejected_preflight_skips_metric_author_and_execution_lineage() -> None:
    rejected_packet, _backend = _review(accept=False)

    class Reviewer:
        config = type("Config", (), {"model_tier": "haiku"})()

        def review_theory_execution_preflight(self, **_kwargs):
            return rejected_packet

    class NeverCalledProvider:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate(self, request):
            self.requests.append(request)
            raise AssertionError("metric author must not run after preflight rejection")

    provider = NeverCalledProvider()
    with pytest.raises(ArchitectMetricSemanticReviewRejected) as exc_info:
        author_reviewed_architect_metric_requirements(
            provider=provider,
            config=ArchitectMetricContractAuthoringConfig(
                model_tier="haiku",
                max_repair_attempts=0,
                metric_semantic_reviewer_max_revisions=0,
            ),
            request_model=TEST_HAIKU_MODEL,
            semantic_reviewer=Reviewer(),  # type: ignore[arg-type]
            repair_ownership_router=None,
            question=_question(),
            runtime_contract={
                "capability_eval_requires_typed_metric_contracts": True,
                "empirical_metric_requirements": [],
                "empirical_metric_protocol_phase": (
                    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED
                ),
                "generated_sandbox_runtime_replicates": 17,
                "simulation_targets": ["evaluate the declared risk"],
            },
            theory_protocol_material=_theory_material(),
        )

    history = exc_info.value.semantic_review_history
    assert provider.requests == []
    assert history[0]["review_stage"] == "theory_execution_preflight"
    assert history[0]["authoring_packet_id"] == ""
    assert history[0]["recommended_repair_scope"] == "upstream_theory"
    assert history[0]["execution_authorized"] is False
    assert history[0]["theory_execution_preflight_packet"] == rejected_packet

    result = architect_preexecution_metric_protocol_rejection_result(
        task=AgentTask(
            task_id="architect:generic-preflight-rejection",
            owner_subsystem="ArchitectCoordinator",
            objective="Route the rejected theory handoff before coding.",
        ),
        question=_question(),
        semantic_review_history=history,
        architect_context={
            "theory_packet_id": "theory_derivation:generic",
            "architect_metric_protocol_gate": {
                "artifact_kind": "RuntimeArchitectMetricProtocolGate",
                "source_theory_packet_id": "theory_derivation:generic",
                "upstream_theory_revision_count": 0,
                "execution_authorized": False,
            },
        },
        max_upstream_theory_revisions=1,
    )
    manifest = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == "RuntimeArchitectMetricProtocolPreExecutionRejection"
    )
    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "TheoryDeveloper"
    assert manifest["disposition"] == "THEORY_EXECUTION_PREFLIGHT_REJECTED"
    assert manifest["preexecution_review_stage"] == "theory_execution_preflight"
    assert manifest["generated_code_observed"] is False
    assert manifest["simulation_results_observed"] is False
    assert result.next_task.inputs["environment_feedback"]["trigger"] == (
        "THEORY_EXECUTION_PREFLIGHT_REQUIRES_UPSTREAM_THEORY_REVISION"
    )


def test_preflight_stops_when_a_revision_closes_no_prior_finding() -> None:
    rejected_packet, _backend = _review(accept=False)
    finding_id = rejected_packet["active_unresolved_finding_ids"][0]
    history = [
        {
            "revision_index": 1,
            "review_stage": "theory_execution_preflight",
            "source_theory_packet_id": "theory_derivation:generic-revision",
            "source_theory_packet_hash": "revised-theory-hash",
            "semantic_review_packet_id": rejected_packet["packet_id"],
            "semantic_review_packet_hash": stable_hash(rejected_packet),
            "overall_verdict": "REVISE",
            "recommended_repair_scope": "upstream_theory",
            "dimension_reviews": rejected_packet["dimension_reviews"],
            "estimator_execution_checks": rejected_packet[
                "estimator_execution_checks"
            ],
            "findings": rejected_packet["findings"],
            "repair_instructions": rejected_packet["repair_instructions"],
            "cumulative_finding_ledger": rejected_packet[
                "cumulative_finding_ledger"
            ],
            "active_unresolved_finding_ids": [finding_id],
            "prior_finding_resolution_summary": {
                "prior_active_finding_ids": [finding_id],
                "resolved_prior_finding_ids": [],
                "still_unresolved_prior_finding_ids": [finding_id],
                "new_finding_ids": [],
                "progress_made": False,
                "stalled": True,
            },
        }
    ]

    result = architect_preexecution_metric_protocol_rejection_result(
        task=AgentTask(
            task_id="architect:generic-preflight-stalled",
            owner_subsystem="ArchitectCoordinator",
            objective="Stop a semantically unchanged theory revision.",
        ),
        question=_question(),
        semantic_review_history=history,
        architect_context={
            "theory_packet_id": "theory_derivation:generic-revision",
            "architect_metric_protocol_gate": {
                "artifact_kind": "RuntimeArchitectMetricProtocolGate",
                "source_theory_packet_id": (
                    "theory_derivation:generic-revision"
                ),
                "upstream_theory_revision_count": 1,
                "execution_authorized": False,
            },
        },
        max_upstream_theory_revisions=2,
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "architect_theory_execution_preflight_stalled"
    )
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["preflight_revision_stalled"] is True
    assert manifest["upstream_theory_revision_routed"] is False


def test_preflight_new_findings_do_not_mask_unresolved_prior_lineage() -> None:
    rejected_packet, _backend = _review(accept=False)
    prior_finding_id = rejected_packet["active_unresolved_finding_ids"][0]
    new_finding_id = "theory:newly_discovered_support_gap"
    history = [
        {
            "revision_index": 1,
            "review_stage": "theory_execution_preflight",
            "source_theory_packet_id": "theory_derivation:generic-revision",
            "source_theory_packet_hash": "revised-theory-hash",
            "semantic_review_packet_id": rejected_packet["packet_id"],
            "semantic_review_packet_hash": stable_hash(rejected_packet),
            "overall_verdict": "REVISE",
            "recommended_repair_scope": "upstream_theory",
            "dimension_reviews": rejected_packet["dimension_reviews"],
            "estimator_execution_checks": rejected_packet[
                "estimator_execution_checks"
            ],
            "findings": [
                {
                    "severity": "medium",
                    "category": "support_coverage_gap",
                    "summary": (
                        "Need explicit support conditions for right-censoring under "
                        "resource bounds."
                    ),
                    "required_change": (
                        "Document finite-horizon behavior as a separate branch."
                    ),
                    "evidence_refs": ["theory.estimator_specs"],
                    "finding_id": prior_finding_id,
                },
                {
                    "severity": "low",
                    "category": "proof_lemma_dependency",
                    "summary": (
                        "Need a finite-outcome support lemma for the new branch."
                    ),
                    "required_change": (
                        "Add a lemma chain for finite-outcome transport."
                    ),
                    "evidence_refs": ["theory.estimator_specs"],
                    "finding_id": new_finding_id,
                },
            ],
            "repair_instructions": rejected_packet["repair_instructions"],
            "cumulative_finding_ledger": rejected_packet[
                "cumulative_finding_ledger"
            ],
            "active_unresolved_finding_ids": [
                prior_finding_id,
                new_finding_id,
            ],
            "prior_finding_resolution_summary": {
                "prior_active_finding_ids": [prior_finding_id],
                "resolved_prior_finding_ids": [],
                "still_unresolved_prior_finding_ids": [prior_finding_id],
                "new_finding_ids": [new_finding_id],
                "progress_made": True,
                "stalled": False,
            },
        }
    ]

    result = architect_preexecution_metric_protocol_rejection_result(
        task=AgentTask(
            task_id="architect:generic-preflight-new-finding",
            owner_subsystem="ArchitectCoordinator",
            objective="Continue revision after reviewer broadens findings.",
        ),
        question=_question(),
        semantic_review_history=history,
        architect_context={
            "theory_packet_id": "theory_derivation:generic-revision",
            "architect_metric_protocol_gate": {
                "artifact_kind": "RuntimeArchitectMetricProtocolGate",
                "source_theory_packet_id": (
                    "theory_derivation:generic-revision"
                ),
                "upstream_theory_revision_count": 1,
                "execution_authorized": False,
            },
        },
        max_upstream_theory_revisions=2,
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "architect_theory_execution_preflight_stalled"
    )
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["preflight_revision_progressed"] is False
    assert manifest["preflight_revision_stalled"] is True
    assert manifest["upstream_theory_revision_routed"] is False

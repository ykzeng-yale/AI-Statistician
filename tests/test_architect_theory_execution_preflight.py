from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ai_statistician.agent_runtime import AgentTask
from ai_statistician.architect_metric_contract_authoring import (
    ArchitectMetricContractAuthoringConfig,
    ArchitectMetricSemanticReviewRejected,
    FRESH_METRIC_AUTHORING_AUTHORITY_KIND,
    _materialize_metric_authoring_model_requirement,
    _metric_authoring_model_requirement_schema,
    author_reviewed_architect_metric_requirements,
)
from ai_statistician.architect_theory_execution_preflight import (
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL,
    _architect_theory_execution_preflight_submit_schema,
    _search_preflight_sources,
    architect_theory_execution_preflight_json_schema,
    build_architect_theory_execution_preflight_material,
    build_architect_theory_execution_preflight_prompt,
    review_architect_theory_execution_preflight,
    validate_architect_theory_execution_preflight_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.structured_output_retry import PacketValidationError
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


def test_fresh_metric_author_owns_semantics_not_provenance_labels() -> None:
    anchor_id = "theory#/guarantee"
    schema = _metric_authoring_model_requirement_schema(
        authority_anchor_ids=[anchor_id]
    )
    predicate_properties = schema["properties"]["predicate_authority"][
        "properties"
    ]
    gate_properties = schema["properties"]["gate_fields"]["items"][
        "properties"
    ]
    assert "authority_kind" not in predicate_properties
    assert "authority_kind" not in gate_properties

    materialized, errors = _materialize_metric_authoring_model_requirement(
        {
            "requirement_id": "generic-risk-bound",
            "metric_semantics": "estimated risk of the generated procedure",
            "metric_value_kind": "numeric",
            "measurement_protocol": "return the empirical risk over fresh replicates",
            "operator": "<=",
            "aggregation": "identity",
            "predicate_authority": {
                "source_anchors": [anchor_id],
                "rationale": "the theory identifies risk as the target quantity",
            },
            "gate_fields": [
                {
                    "field": "threshold",
                    "value": 0.1,
                    "source_anchors": [anchor_id],
                    "rationale": "pre-execution decision threshold",
                }
            ],
        },
        requirement_index=0,
    )

    assert errors == []
    assert materialized["threshold"] == 0.1
    assert materialized["acceptance_authority_kind"] == (
        FRESH_METRIC_AUTHORING_AUTHORITY_KIND
    )
    assert materialized["gate_field_authorities"][0]["authority_kind"] == (
        FRESH_METRIC_AUTHORING_AUTHORITY_KIND
    )


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
        self.repair_payload = {}

    def generate(self, request):
        self.requests.append(request)
        if len(self.requests) == 1:
            payload = self.initial_payload
        else:
            self.repair_payload = json.loads(
                request.user_prompt.split("\n\n", 1)[1]
            )
            payload = deepcopy(self.initial_payload)
            primitive_index = ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS.index(
                "primitive_mathematical_consistency"
            )
            payload["dimension_reviews"][primitive_index]["evidence_refs"] = [
                "theory.estimator_specs"
            ]
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
        cite_sources: bool = True,
    ) -> None:
        self.accept = accept
        self.payload = deepcopy(payload) if payload is not None else None
        self.submit_before_search = submit_before_search
        self.submit_unknown_ref_once = submit_unknown_ref_once
        self.source_scope = source_scope
        self.cite_sources = cite_sources
        self.requests = []
        self.hit_id = ""
        self.source_ref = ""

    def _submission(self, *, source_ref: str) -> dict[str, object]:
        payload = deepcopy(self.payload) if self.payload is not None else _payload(
            accept=self.accept
        )
        if self.cite_sources:
            for finding in payload["findings"]:
                finding["source_evidence_refs"] = [source_ref]
            for review in payload.get("prior_finding_reviews", []) or []:
                review["source_evidence_refs"] = [source_ref]
        for field in (
            "dimension_reviews",
            "estimator_execution_checks",
        ):
            rows = payload.get(field)
            if isinstance(rows, list):
                payload[field] = {
                    f"slot_{index}": row for index, row in enumerate(rows)
                }
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
                "identity_check": (
                    "On a finite two-observation input with one event, the primitive "
                    "first-event definition returns "
                    "the position of the event, with a typed censored output if absent; "
                    "the declared candidate returns that same index or censored output."
                ),
                "blocking_gaps": (
                    []
                    if accept
                    else [
                        "The stopped finite observation is not connected to the ideal risk."
                    ]
                ),
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
                    "observed_behavior": (
                        "A finite input can end before the ideal event, leaving the "
                        "declared executable output undefined."
                    ),
                    "expected_behavior": (
                        "Every admitted finite input has a typed outcome whose "
                        "relationship to the requested estimand is explicit."
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
        max_validation_retries=0,
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
        max_validation_retries=0,
        source_retriever=source_retriever,
        prior_finding_ledger=prior_finding_ledger,
    )


def test_preflight_client_tool_loop_searches_before_grounded_submission() -> None:
    backend = _PreflightToolBackend(accept=False)

    packet = _tool_review(backend)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["source_grounding_required"] is True
    assert packet["source_grounding_transport"] == (
        "client_tool_optional_source_query_v8"
    )
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
    assert backend.requests[0].tools[0].strict is False
    assert backend.requests[0].tools[1].strict is True
    assert backend.requests[0].metadata["model_tier"] == "haiku"
    assert backend.requests[0].disable_parallel_tool_use is False
    first_result = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert first_result["hits"][0]["source_ref"] == "S1H1"


def test_preflight_canonicalizes_prior_finding_source_ref_before_binding() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_id = rejected["active_unresolved_finding_ids"][0]
    prior_finding = prior_ledger[0]["finding"]
    payload = _payload(accept=False)
    payload["findings"] = []
    payload["prior_finding_reviews"] = [
        {
            "status": "UNRESOLVED",
            "rationale": "The revised source still leaves the finite branch undefined.",
            "evidence_refs": ["theory.estimator_specs"],
        }
    ]
    backend = _PreflightToolBackend(accept=False, payload=payload)

    packet = _tool_review(backend, prior_finding_ledger=prior_ledger)

    continued = packet["findings"][0]
    assert continued["finding_id"] == prior_finding_id
    assert continued["source_evidence_refs"] == [backend.hit_id]
    for field in (
        "severity",
        "category",
        "summary",
        "observed_behavior",
        "expected_behavior",
        "evidence_refs",
    ):
        assert continued[field] == prior_finding[field]
    binding = packet["runtime_prior_finding_identity_bindings"][0]
    assert binding["semantic_source"] == "active_prior_finding_ledger"
    assert binding["prior_ledger_semantic_fingerprint"] == (
        binding["carried_semantic_fingerprint"]
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
    assert "not returned by the runtime" in failed_submit["result_excerpt"]
    assert "available handles: S1H1" in failed_submit["result_excerpt"]
    rejection = json.loads(failed_submit["result_excerpt"])
    assert rejection["error"] == "preflight_submission_rejected"
    assert "theory.estimator_specs" in rejection["field_contracts"][
        "evidence_refs"
    ]["allowed_values"]
    assert "S1H1" in rejection["field_contracts"]["source_evidence_refs"][
        "allowed_values"
    ]


def test_preflight_client_tool_loop_returns_all_pass_finding_conflict_to_model() -> None:
    class AllPassFindingBackend(_PreflightToolBackend):
        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "search-1",
                        "search_preflight_sources",
                        {
                            "query": "finite input censored outcome",
                            "source_scope": "theory",
                            "k": 4,
                        },
                    )
                )
            result = json.loads(request.messages[-1]["content"][0]["content"])
            if result.get("hits"):
                self.hit_id = result["hits"][0]["source_hit_id"]
                self.source_ref = result["hits"][0]["source_ref"]
            if turn == 2:
                payload = _payload(accept=True)
                payload["findings"] = deepcopy(_payload(accept=False)["findings"])
                payload["findings"][0]["source_evidence_refs"] = [self.source_ref]
                return _tool_response(
                    ClientToolCall(
                        "submit-inconsistent",
                        "submit_theory_preflight_review",
                        payload,
                    )
                )
            assert result["error"] == "preflight_submission_rejected"
            assert any(
                "contradict the all-PASS" in error
                for error in result["validation_errors"]
            )
            return _tool_response(
                ClientToolCall(
                    "submit-consistent",
                    "submit_theory_preflight_review",
                    _payload(accept=True),
                )
            )

    backend = AllPassFindingBackend(accept=True)

    packet = _tool_review(backend)

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["findings"] == []
    assert len(backend.requests) == 3
    assert {request.model for request in backend.requests} == {TEST_HAIKU_MODEL}
    rejected = packet["client_tool_loop_history"][1]["tool_calls"][0]
    assert rejected["name"] == "submit_theory_preflight_review"
    assert rejected["is_error"] is True
    assert "contradict the all-PASS" in rejected["result_excerpt"]


def test_preflight_repairs_swapped_citation_namespaces_from_structured_feedback() -> None:
    class SwappedCitationBackend(_PreflightToolBackend):
        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "search-1",
                        "search_preflight_sources",
                        {
                            "query": "finite input censored outcome",
                            "source_scope": "theory",
                            "k": 4,
                        },
                    )
                )
            result = json.loads(request.messages[-1]["content"][0]["content"])
            if result.get("hits"):
                self.hit_id = result["hits"][0]["source_hit_id"]
                self.source_ref = result["hits"][0]["source_ref"]
            if turn == 2:
                payload = self._submission(source_ref="theory.estimator_specs")
                payload["findings"][0]["evidence_refs"] = [self.source_ref]
                return _tool_response(
                    ClientToolCall(
                        "submit-swapped-refs",
                        "submit_theory_preflight_review",
                        payload,
                    )
                )
            assert result["error"] == "preflight_submission_rejected"
            assert result["field_contracts"]["evidence_refs"][
                "allowed_values"
            ]
            assert self.source_ref in result["field_contracts"][
                "source_evidence_refs"
            ]["allowed_values"]
            return _tool_response(
                ClientToolCall(
                    "submit-repaired-refs",
                    "submit_theory_preflight_review",
                    self._submission(source_ref=self.source_ref),
                )
            )

    backend = SwappedCitationBackend(accept=False)

    packet = _tool_review(backend)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["client_tool_loop_turns"] == 3
    rejected = packet["client_tool_loop_history"][1]["tool_calls"][0]
    assert rejected["is_error"] is True
    rejection = json.loads(rejected["result_excerpt"])
    assert "theory execution preflight uses missing or unknown evidence refs" in (
        rejection["validation_errors"]
    )
    assert packet["findings"][0]["source_evidence_refs"] == [backend.hit_id]


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
        "submit_theory_preflight_review",
    ]
    assert [tool.name for tool in backend.requests[4].tools] == [
        "submit_theory_preflight_review",
    ]
    assert backend.requests[4].metadata[
        "client_tool_loop_max_terminal_recovery_turns"
    ] == 1
    failed_submit = packet["client_tool_loop_history"][3]["tool_calls"][0]
    assert failed_submit["is_error"] is True
    assert packet["client_tool_loop_turns"] == 5


def test_preflight_client_tool_loop_allows_model_to_submit_without_search() -> None:
    backend = _PreflightToolBackend(
        accept=False,
        submit_before_search=True,
    )

    packet = _tool_review(backend)

    assert len(backend.requests) == 1
    first_submit = packet["client_tool_loop_history"][0]["tool_calls"][0]
    assert first_submit["is_error"] is False
    assert packet["preflight_source_search_count"] == 0
    assert packet["source_grounding_required"] is False
    assert "source_evidence_refs" not in packet["findings"][0]


def test_preflight_search_does_not_force_every_finding_to_cite_rag() -> None:
    backend = _PreflightToolBackend(accept=False, cite_sources=False)

    packet = _tool_review(backend)

    assert len(backend.requests) == 2
    assert packet["preflight_source_search_count"] == 1
    assert packet["source_grounding_required"] is True
    assert "source_evidence_refs" not in packet["findings"][0]
    assert packet["source_grounding_bindings"] == []


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

    assert len(backend.requests) == 5
    assert all(
        [tool.name for tool in request.tools]
        == ["submit_theory_preflight_review"]
        for request in backend.requests[-2:]
    )
    assert backend.requests[-1].metadata[
        "client_tool_loop_terminal_decision_reason"
    ] == "repeated turns without a client tool call"
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
    verdict_policy = prompt_payload["verdict_policy"]
    assert "checkable derivation" in verdict_policy
    assert "hypotheses to audit, not independent evidence" in verdict_policy
    assert "substitute it into the current displayed formula" in verdict_policy
    assert "actually necessary for the stated execution gate" in verdict_policy
    assert "absence of an explicit rebuttal" in verdict_policy
    assert "Retract a prior finding when its premise is false" in verdict_policy
    assert "one to three concise sentences" in verdict_policy
    assert "do not quote or restate" in verdict_policy
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
        "preflight has no generated-code or simulation authority",
        "leave that check to the existing AlgorithmEngineer or SimulationEngineer",
    ):
        assert phrase in protocol
    assert packet["overall_verdict"] == "ACCEPT"
    assert "runtime_estimator_status_normalizations" not in packet
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
    assert "theory.rejected_alternatives" in anchor_ids
    assert "theory.self_critique" not in anchor_ids
    assert "theory.critic_findings" not in anchor_ids
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
    assert backend.requests[0].max_tokens == 7000
    assert backend.requests[0].metadata["review_output_token_cap"] == 8000
    assert "not theorem peer review" in backend.requests[0].system_prompt
    assert "Exclude downstream proof obligations" in (
        backend.requests[0].schema["properties"]["findings"]["description"]
    )
    dimension_schema = backend.requests[0].schema["properties"][
        "dimension_reviews"
    ]
    assert dimension_schema["type"] == "object"
    expected_dimension_slots = [
        f"slot_{index}"
        for index in range(len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_DIMENSIONS))
    ]
    assert dimension_schema["required"] == expected_dimension_slots
    assert set(dimension_schema["properties"]) == set(expected_dimension_slots)
    assert all(
        row == {"$ref": "#/$defs/dimension_review"}
        for row in dimension_schema["properties"].values()
    )
    estimator_schema = backend.requests[0].schema["properties"][
        "estimator_execution_checks"
    ]
    assert estimator_schema["type"] == "object"
    assert estimator_schema["required"] == ["slot_0"]
    assert estimator_schema["properties"]["slot_0"] == {
        "$ref": "#/$defs/estimator_execution_check"
    }
    assert "estimator_id" not in backend.requests[0].schema["$defs"][
        "estimator_execution_check"
    ]["properties"]
    assert "repair_instructions" not in backend.requests[0].schema["properties"]
    assert prompt_payload["ordered_review_slots"][
        "estimator_execution_checks"
    ] == [{"output_slot": "slot_0", "estimator_id": "generic_stream_method"}]
    assert "prior_finding_reviews" not in backend.requests[0].schema[
        "properties"
    ]
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_source_search_exposes_late_theory_entries() -> None:
    theory_material = _theory_material()
    derivation = theory_material["theory_semantic_material"][
        "theory_derivation_packet"
    ]
    derivation["derivation_steps"] = [
        {
            "id": f"claim_{index + 1}",
            "claim": f"Generic derivation claim {index + 1}",
            "equation_or_argument": (
                "late_entry_visibility_marker"
                if index == 11
                else f"argument {index + 1}"
            ),
        }
        for index in range(12)
    ]
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=theory_material,
        upstream_research_contract={"simulation_targets": ["evaluate risk"]},
    )

    derivation_anchor = next(
        row
        for row in material["anchor_catalog"]
        if row["anchor_id"] == "theory.derivation_steps"
    )
    observation = _search_preflight_sources(
        material=material,
        source_retriever=None,
        query="late_entry_visibility_marker",
        source_scope="theory",
        k=3,
        search_index=1,
    )
    prompt = build_architect_theory_execution_preflight_prompt(material)
    prompt_payload = json.loads(prompt.split("\n\n", 1)[1])
    derivation_source = next(
        row
        for row in prompt_payload["source_material"]["current_theory_anchors"]
        if row["anchor_id"] == "theory.derivation_steps"
    )

    assert len(derivation_anchor["content"]) == 12
    assert "late_entry_visibility_marker" in prompt
    assert len(derivation_source["content"]) == 12
    assert derivation_source["content"][-1]["id"] == "claim_12"
    assert observation["hits"][0]["location"] == "theory.derivation_steps/11"
    assert observation["hits"][0]["content"]["equation_or_argument"] == (
        "late_entry_visibility_marker"
    )


def test_preflight_full_regeneration_returns_raw_validation_feedback() -> None:
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
        max_validation_retries=1,
    )

    assert "subsystem_repair_context" not in backend.repair_payload
    assert any(
        "unknown evidence refs" in error
        for error in backend.repair_payload["local_validation_errors"]
    )
    assert backend.repair_payload["original_request"] == (
        backend.requests[0].user_prompt
    )
    assert "unknown.anchor" in backend.repair_payload["previous_candidate"]
    assert packet["overall_verdict"] == "REVISE"
    assert packet["structured_output_retry_history"][1]["retry_mode"] == (
        "full_packet_regeneration"
    )


def test_preflight_prior_finding_schema_uses_compact_ordered_array() -> None:
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
    assert len(json.dumps(six_schema, separators=(",", ":"))) - len(
        json.dumps(one_schema, separators=(",", ":"))
    ) < 400


def test_preflight_v344_shape_survives_anthropic_strict_transform() -> None:
    anthropic = pytest.importorskip("anthropic")
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    material["required_estimator_ids"] = ["estimator_a", "estimator_b"]
    material["active_prior_finding_ids"] = [
        "finding:0",
        "finding:1",
        "finding:2",
    ]
    schema = _architect_theory_execution_preflight_submit_schema(material)
    transformed = anthropic.transform_schema(schema)

    for field in (
        "dimension_reviews",
        "estimator_execution_checks",
    ):
        assert transformed["properties"][field]["required"] == (
            schema["properties"][field]["required"]
        )
    transformed_prior = transformed["properties"]["prior_finding_reviews"]
    assert transformed_prior["type"] == "array"
    assert "maxItems: 3" in transformed_prior["description"]
    assert "minItems: 3" in transformed_prior["description"]
    estimator_properties = transformed["$defs"][
        "estimator_execution_check"
    ]["properties"]
    assert set(estimator_properties) == {
        "audit_rationale",
        "identity_check",
        "blocking_gaps",
        "boundary_or_counterexample",
        "status",
        "evidence_refs",
    }
    assert len(json.dumps(transformed, separators=(",", ":"))) < 7_500


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
        "identity_check",
        "blocking_gaps",
        "boundary_or_counterexample",
        "status",
        "evidence_refs",
    ]
    assert set(estimator_schema["properties"]) == set(
        estimator_schema["required"]
    )
    assert estimator_schema["properties"]["audit_rationale"]["maxLength"] == 900
    assert estimator_schema["properties"]["blocking_gaps"]["maxItems"] == 6


def test_preflight_cannot_accept_a_failed_independent_identity_check() -> None:
    packet, _backend = _review(accept=True)
    packet["estimator_execution_checks"][0]["blocking_gaps"] = [
        "The independent primitive recomputation does not match the candidate output."
    ]
    packet["estimator_execution_checks"][0]["status"] = "FAIL"
    packet["overall_verdict"] = "REVISE"

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=build_architect_theory_execution_preflight_material(
            question=_question(),
            theory_protocol_material=_theory_material(),
            upstream_research_contract={
                "simulation_targets": ["evaluate the declared risk"]
            },
        ),
    )

    assert any("needs at least one finding" in error for error in errors)


def test_preflight_cannot_accept_pass_with_a_model_reported_blocking_gap() -> None:
    packet, _backend = _review(accept=True)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    packet["estimator_execution_checks"][0]["blocking_gaps"] = [
        "The source does not establish its claimed procedure identity."
    ]

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )

    assert any(
        "status=PASS cannot report blocking_gaps" in error
        and "estimator_id='generic_stream_method'" in error
        for error in errors
    )
    assert any("overall verdict is not runtime-derived" in error for error in errors)


def test_preflight_nonpass_estimator_requires_a_model_authored_blocking_gap() -> None:
    packet, _backend = _review(accept=True)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    packet["estimator_execution_checks"][0]["status"] = "UNCERTAIN"
    packet["estimator_execution_checks"][0]["blocking_gaps"] = []

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )

    assert any(
        "status=UNCERTAIN requires a model-authored blocking gap" in error
        and "estimator_id='generic_stream_method'" in error
        for error in errors
    )
    assert any("overall verdict is not runtime-derived" in error for error in errors)


def test_preflight_preserves_model_owned_dimension_and_estimator_judgments() -> None:
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
        max_validation_retries=1,
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
    assert "derived_consistency_warnings" not in packet
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_returns_inconsistent_estimator_pass_to_same_model() -> None:
    payload = _payload(accept=True)
    payload["dimension_reviews"][1] = {
        "status": "UNCERTAIN",
        "rationale": "One invoked theorem hypothesis is not established.",
        "evidence_refs": ["theory.theorem_cards", "theory.estimator_specs"],
    }
    payload["estimator_execution_checks"][0]["blocking_gaps"] = [
        "The source does not establish every invoked theorem hypothesis."
    ]
    payload["estimator_execution_checks"][0][
        "audit_rationale"
    ] = "The source does not establish every invoked theorem hypothesis."
    payload["findings"] = [
        {
            "severity": "high",
            "category": "unestablished_theorem_hypothesis",
            "summary": "An invoked theorem hypothesis remains unestablished.",
            "observed_behavior": (
                "The estimator row reports PASS while also reporting a blocking gap."
            ),
            "expected_behavior": (
                "The estimator status agrees with its model-authored blocker list."
            ),
            "evidence_refs": ["theory.theorem_cards", "theory.estimator_specs"],
        }
    ]

    class Backend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate(self, request):
            self.requests.append(request)
            candidate = deepcopy(payload)
            if len(self.requests) > 1:
                candidate["estimator_execution_checks"][0]["status"] = "UNCERTAIN"
            return GeneratorResponse(
                text=json.dumps(candidate),
                provider="anthropic",
                model=request.model,
                metadata={
                    "provider_structured_output_requested": True,
                    "provider_structured_output_applied": True,
                },
            )

    backend = Backend()

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
        max_validation_retries=1,
    )
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )

    assert len(backend.requests) == 2
    estimator_row = packet["estimator_execution_checks"][0]
    assert estimator_row["status"] == "UNCERTAIN"
    assert estimator_row["blocking_gaps"] == [
        "The source does not establish every invoked theorem hypothesis."
    ]
    assert packet["overall_verdict"] == "REVISE"
    assert packet["findings"][0]["category"] == (
        "unestablished_theorem_hypothesis"
    )
    assert "runtime_estimator_status_normalizations" not in packet
    assert packet["structured_output_retry_attempts"] == 1
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_regenerates_all_pass_finding_conflict_with_same_model() -> None:
    class AllPassFindingBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.regeneration_payload = {}

        def generate(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = _payload(accept=True)
                payload["findings"] = deepcopy(_payload(accept=False)["findings"])
            else:
                self.regeneration_payload = json.loads(
                    request.user_prompt.split("\n\n", 1)[1]
                )
                payload = _payload(accept=True)
            return GeneratorResponse(
                text=json.dumps(payload),
                provider="anthropic",
                model=request.model,
                metadata={
                    "provider_structured_output_requested": True,
                    "provider_structured_output_applied": True,
                },
            )

    backend = AllPassFindingBackend()

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
        max_validation_retries=1,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["findings"] == []
    assert packet["structured_output_retry_attempts"] == 1
    assert len(backend.requests) == 2
    assert {request.model for request in backend.requests} == {TEST_HAIKU_MODEL}
    assert any(
        "contradict the all-PASS" in error
        for error in backend.regeneration_payload["local_validation_errors"]
    )


def test_preflight_reports_semantic_mismatch_without_selecting_an_owner() -> None:
    packet, _backend = _review(accept=False)

    assert packet["overall_verdict"] == "REVISE"
    finding = packet["findings"][0]
    assert finding["observed_behavior"]
    assert finding["expected_behavior"]
    assert "repair_scope" not in finding
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
        max_validation_retries=0,
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
    prompt_payload = json.loads(
        backend.requests[0].user_prompt.split("\n\n", 1)[1]
    )
    prior_slot = prompt_payload["ordered_review_slots"][
        "prior_finding_reviews"
    ][0]
    assert prior_slot["finding_id"] == prior_finding_ids[0]
    assert prior_slot["prior_obligation"]["summary"] == (
        prior_ledger[0]["finding"]["summary"]
    )
    assert "observed_behavior" not in prior_slot["prior_obligation"]
    assert prior_ledger[0]["finding"]["observed_behavior"] not in (
        backend.requests[0].user_prompt
    )
    assert prior_slot["prior_obligation"]["expected_behavior"] == (
        prior_ledger[0]["finding"]["expected_behavior"]
    )
    assert prior_slot["review_basis"] == "current_theory_anchors_only"
    assert "finding_id" not in prior_review_definition["properties"]
    assert "current_finding" not in prior_review_definition["properties"]
    finding_definition = backend.requests[0].schema["$defs"]["finding"]
    assert finding_definition["properties"]["prior_finding_index"] == {
        "type": "integer",
        "minimum": -1,
        "maximum": 0,
        "description": (
            "Select the ordered prior-finding slot with the same invariant or "
            "required remedy. Use -1 only for a genuinely new defect."
        ),
    }
    assert "prior_finding_index" in finding_definition["required"]
    assert accepted["overall_verdict"] == "ACCEPT"
    assert accepted["active_unresolved_finding_ids"] == []
    assert accepted["runtime_prior_finding_identity_bindings"] == []
    assert accepted["prior_finding_resolution_summary"] == {
        "prior_active_finding_ids": prior_finding_ids,
        "resolved_prior_finding_ids": prior_finding_ids,
        "retracted_prior_finding_ids": [],
        "closed_prior_finding_ids": prior_finding_ids,
        "still_unresolved_prior_finding_ids": [],
        "new_finding_ids": [],
        "progress_made": True,
        "stalled": False,
    }
    assert accepted["cumulative_finding_ledger"][0]["status"] == (
        "RESOLVED_BY_CURRENT_THEORY"
    )


def test_preflight_can_retract_prior_finding_from_current_evidence() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_ids = rejected["active_unresolved_finding_ids"]

    accepted_payload = _payload(accept=True)
    accepted_payload["prior_finding_reviews"] = [
        {
            "status": "RETRACTED_BY_CURRENT_EVIDENCE",
            "rationale": (
                "Current source anchors show the prior concern is outside the "
                "admitted finite interface and is not a pre-execution blocker."
            ),
            "evidence_refs": ["theory.estimator_specs"],
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
        max_validation_retries=0,
        prior_finding_ledger=prior_ledger,
    )

    prior_status_schema = backend.requests[0].schema["$defs"][
        "prior_finding_review"
    ]["properties"]["status"]
    assert "RETRACTED_BY_CURRENT_EVIDENCE" in prior_status_schema["enum"]
    assert accepted["overall_verdict"] == "ACCEPT"
    assert accepted["active_unresolved_finding_ids"] == []
    assert accepted["prior_finding_resolution_summary"] == {
        "prior_active_finding_ids": prior_finding_ids,
        "resolved_prior_finding_ids": [],
        "retracted_prior_finding_ids": prior_finding_ids,
        "closed_prior_finding_ids": prior_finding_ids,
        "still_unresolved_prior_finding_ids": [],
        "new_finding_ids": [],
        "progress_made": True,
        "stalled": False,
    }
    assert accepted["cumulative_finding_ledger"][0]["status"] == (
        "RETRACTED_BY_CURRENT_EVIDENCE"
    )


def test_preflight_binds_unresolved_prior_finding_from_ordered_index() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_id = rejected["active_unresolved_finding_ids"][0]
    prior_finding = prior_ledger[0]["finding"]
    initial_payload = _payload(accept=False)
    initial_payload["findings"] = [
        {
            "prior_finding_index": -1,
            "severity": "medium",
            "category": "new_finite_branch_gap",
            "summary": "A separate finite branch also needs an explicit outcome.",
            "observed_behavior": "The separate finite branch has no declared output.",
            "expected_behavior": "Every finite branch has a typed declared output.",
            "evidence_refs": ["theory.estimator_specs"],
        }
    ]
    initial_payload["prior_finding_reviews"] = [
        {
            "status": "UNRESOLVED",
            "rationale": "The revised source still leaves the finite branch undefined.",
            "evidence_refs": ["theory.estimator_specs"],
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
        max_validation_retries=0,
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 1
    finding_schema = backend.requests[0].schema["$defs"]["finding"]
    assert "prior_finding_id" not in finding_schema["properties"]
    assert finding_schema["properties"]["prior_finding_index"]["maximum"] == 0
    assert "finding_id" not in finding_schema["properties"]
    prior_schema = backend.requests[0].schema["properties"][
        "prior_finding_reviews"
    ]["items"]
    assert prior_schema == {"$ref": "#/$defs/prior_finding_review"}
    assert "current_finding" not in backend.requests[0].schema["$defs"][
        "prior_finding_review"
    ]["properties"]
    assert packet["findings"][0]["prior_finding_id"] == prior_finding_id
    assert packet["findings"][0]["finding_id"] == prior_finding_id
    assert packet["findings"][0]["summary"] == prior_finding["summary"]
    assert packet["findings"][1].get("prior_finding_id", "") == ""
    binding = packet["runtime_prior_finding_identity_bindings"][0]
    assert binding["prior_finding_id"] == prior_finding_id
    assert binding["semantic_source"] == "active_prior_finding_ledger"
    assert binding["prior_ledger_semantic_fingerprint"] == (
        binding["carried_semantic_fingerprint"]
    )
    assert binding["runtime_selected_semantics"] is False
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


def test_preflight_prior_lineage_errors_name_expected_and_missing_ids() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_id = rejected["active_unresolved_finding_ids"][0]
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        prior_finding_ledger=prior_ledger,
    )
    packet = deepcopy(rejected)
    packet["source_theory_packet_id"] = material["source_theory_packet_id"]
    packet["source_theory_packet_hash"] = material["source_theory_packet_hash"]
    packet["anchor_catalog_id"] = material["anchor_catalog_id"]
    packet["anchor_catalog_fingerprint"] = material[
        "anchor_catalog_fingerprint"
    ]
    packet["review_input_fingerprint"] = stable_hash(dict(material))
    packet["prior_finding_reviews"] = []
    packet["findings"] = []
    packet["runtime_prior_finding_identity_bindings"] = []

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )

    lineage_error = next(
        error
        for error in errors
        if error.startswith(
            "theory execution preflight must resolve every active prior"
        )
    )
    assert json.dumps([prior_finding_id]) in lineage_error
    assert "observed=[]" in lineage_error

    packet["prior_finding_reviews"] = [
        {
            "finding_id": prior_finding_id,
            "status": "UNRESOLVED",
            "rationale": "The current source still leaves the defect open.",
            "evidence_refs": ["theory.estimator_specs"],
        }
    ]
    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )
    continuation_error = next(
        error
        for error in errors
        if error.startswith("runtime must carry each UNRESOLVED prior finding")
    )
    assert json.dumps([prior_finding_id]) in continuation_error


def test_preflight_binds_paraphrased_restatement_by_model_selected_prior_slot() -> None:
    rejected, _backend = _review(accept=False)
    prior_ledger = rejected["cumulative_finding_ledger"]
    prior_finding_id = rejected["active_unresolved_finding_ids"][0]
    initial_payload = _payload(accept=False)
    initial_payload["findings"] = [
        {
            "prior_finding_index": 0,
            "severity": "critical",
            "category": "paraphrased_current_failure",
            "summary": "Different words describe the same required finite outcome.",
            "observed_behavior": "The revised source still omits that outcome.",
            "expected_behavior": "The same finite branch must remain total and typed.",
            "evidence_refs": ["theory.estimator_specs"],
        }
    ]
    initial_payload["prior_finding_reviews"] = [
        {
            "status": "UNRESOLVED",
            "rationale": "The finite source branch remains undefined.",
            "evidence_refs": ["theory.estimator_specs"],
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
        max_validation_retries=1,
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 1
    assert "current_finding" not in backend.requests[0].schema["$defs"][
        "prior_finding_review"
    ]["properties"]
    assert packet["findings"][0]["prior_finding_id"] == prior_finding_id
    assert packet["findings"][0]["finding_id"] == prior_finding_id
    assert packet["findings"][0]["summary"] == prior_ledger[0]["finding"][
        "summary"
    ]
    assert len(packet["findings"]) == 1
    assert packet["prior_finding_resolution_summary"]["new_finding_ids"] == []
    assert packet["runtime_prior_finding_identity_bindings"][0][
        "runtime_selected_semantics"
    ] is False
    assert packet["structured_output_retry_attempts"] == 0


def test_preflight_regenerates_missing_ordered_prior_row() -> None:
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
        }
        for _finding_id in prior_finding_ids
    ]
    initial_payload = _payload(accept=True)
    initial_payload["prior_finding_reviews"] = resolved_rows[:1]

    class MissingPriorRowBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.retry_payload = {}

        def generate(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = initial_payload
            else:
                repair_payload = json.loads(request.user_prompt.split("\n\n", 1)[1])
                self.retry_payload = repair_payload
                payload = deepcopy(initial_payload)
                payload["prior_finding_reviews"] = deepcopy(resolved_rows)
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
        max_validation_retries=1,
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 2
    assert "subsystem_repair_context" not in backend.retry_payload
    assert all(
        finding_id in backend.retry_payload["original_request"]
        for finding_id in prior_finding_ids
    )
    assert [
        row["finding_id"] for row in packet["prior_finding_reviews"]
    ] == prior_finding_ids
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["structured_output_retry_attempts"] == 1


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
                max_validation_retries=0,
                metric_semantic_reviewer_max_revisions=0,
            ),
            request_model=TEST_HAIKU_MODEL,
            semantic_reviewer=Reviewer(),  # type: ignore[arg-type]
            question=_question(),
            runtime_contract={
                "research_evaluation_requires_typed_metric_contracts": True,
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
    assert "recommended_repair_scope" not in history[0]
    assert "repair_instructions" not in history[0]
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
    assert "runtime_architect_operation" not in result.next_task.inputs
    assert manifest["disposition"] == "THEORY_EXECUTION_PREFLIGHT_REJECTED"
    assert manifest["preexecution_review_stage"] == "theory_execution_preflight"
    assert manifest["generated_code_observed"] is False
    assert manifest["simulation_results_observed"] is False
    authority = manifest["preexecution_evidence_authority"]
    assert authority["empirical_measurements_observed"] is False
    assert authority["numeric_execution_claims_authoritative"] is False
    assert result.next_task.inputs["environment_feedback"]["trigger"] == (
        "THEORY_EXECUTION_PREFLIGHT_REJECTED"
    )
    assert result.next_task.inputs["environment_feedback"][
        "preexecution_evidence_authority"
    ] == authority
    assert "architect_route_required" not in result.next_task.inputs[
        "environment_feedback"
    ]
    assert "source_workspace_return_required" not in result.next_task.inputs[
        "environment_feedback"
    ]
    assert "runtime_selected_owner" not in result.next_task.inputs[
        "environment_feedback"
    ]


def test_metric_review_exhaustion_blocks_in_source_workspace() -> None:
    history = [
        {
            "revision_index": 1,
            "review_stage": "metric_contract_review",
            "source_theory_packet_id": "theory_derivation:generic",
            "source_theory_packet_hash": "generic-theory-hash",
            "authoring_packet_id": "metric-authoring:revision-1",
            "semantic_review_packet_id": "metric-review:revision-1",
            "overall_verdict": "REVISE",
            "findings": [
                {
                    "finding_id": "metric:interface-mismatch",
                    "severity": "high",
                    "category": "runtime_interface",
                    "summary": "The declared metric output does not match the consumer.",
                    "observed_behavior": "The metric returns a vector.",
                    "expected_behavior": "The consumer requires one scalar.",
                    "evidence_refs": ["metric_contract.output"],
                }
            ],
            "active_unresolved_finding_ids": ["metric:interface-mismatch"],
        }
    ]

    result = architect_preexecution_metric_protocol_rejection_result(
        task=AgentTask(
            task_id="architect:generic-metric-rejection",
            owner_subsystem="ArchitectCoordinator",
            objective="Record bounded metric-authoring exhaustion.",
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
        max_upstream_theory_revisions=2,
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "architect_metric_protocol_source_workspace_exhausted"
    )
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["architect_route_requested"] is False
    assert manifest["upstream_theory_revision_routed"] is False
    assert manifest["upstream_theory_revision_count"] == 0
    assert len(manifest["semantic_review_history"]) == 1
    assert result.evidence_entries[0].status == (
        "PREEXECUTION_PROTOCOL_REJECTED_SOURCE_WORKSPACE_EXHAUSTED"
    )


def test_preflight_uses_remaining_global_budget_when_no_prior_finding_closes() -> None:
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
            "dimension_reviews": rejected_packet["dimension_reviews"],
            "estimator_execution_checks": rejected_packet[
                "estimator_execution_checks"
            ],
            "findings": rejected_packet["findings"],
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

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "TheoryDeveloper"
    assert result.failure_classification == (
        "theory_execution_preflight_returned_to_source_workspace"
    )
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["preflight_revision_stalled"] is True
    assert manifest["upstream_theory_revision_routed"] is True
    assert manifest["architect_route_requested"] is False
    assert "source_workspace_return_requested" not in manifest
    assert manifest["runtime_selected_owner"] is False
    progress = result.next_task.inputs["environment_feedback"][
        "progress_observation"
    ]
    assert progress["same_lineage_no_progress_observed"] is True
    assert progress["runtime_selected_disposition"] is False


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
                    "observed_behavior": (
                        "The finite-horizon branch has no explicit support condition."
                    ),
                    "expected_behavior": (
                        "The admitted support conditions cover every finite-horizon "
                        "branch."
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
                    "observed_behavior": (
                        "The finite-outcome transport claim has no supporting lemma."
                    ),
                    "expected_behavior": (
                        "The transport claim is linked to a source-grounded argument."
                    ),
                    "evidence_refs": ["theory.estimator_specs"],
                    "finding_id": new_finding_id,
                },
            ],
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

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "TheoryDeveloper"
    assert result.failure_classification == (
        "theory_execution_preflight_returned_to_source_workspace"
    )
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["preflight_revision_progressed"] is False
    assert manifest["preflight_revision_stalled"] is True
    assert manifest["upstream_theory_revision_routed"] is True
    assert manifest["architect_route_requested"] is False
    assert "source_workspace_return_requested" not in manifest
    assert manifest["runtime_selected_owner"] is False

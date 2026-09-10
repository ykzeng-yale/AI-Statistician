from __future__ import annotations

import hashlib
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

from ai_statistician.agent_runtime import (
    AgentTask,
    BlackboardState,
    RUNTIME_CONTINUATION_BUDGET_MARKER_KEY,
)
from ai_statistician.client_tool_loop import (
    ClientToolInputError,
)
from ai_statistician.architect_metric_contract_authoring import (
    ArchitectMetricContractAuthoringConfig,
    ArchitectMetricSemanticReviewRejected,
    METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
    METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
    METRIC_PROTOCOL_WORKSPACE_INITIAL_DOCUMENT,
    METRIC_PROTOCOL_WORKSPACE_READ_TOOL,
    METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT,
    _materialize_source_acceptance_protocol,
    _run_metric_protocol_workspace,
    author_reviewed_architect_metric_requirements,
    build_architect_upstream_research_contract,
)
from ai_statistician.architect_theory_execution_preflight import (
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_COMPARE_REVISION_TOOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_AUTHOR_SCRATCH_TOOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WORKSPACE_CHECKPOINT_KIND,
    PREFLIGHT_EXECUTION_HANDOFF_BLOCKED,
    PREFLIGHT_EXECUTION_HANDOFF_NOT_REQUIRED,
    PREFLIGHT_EXECUTION_HANDOFF_READY,
    _architect_theory_execution_preflight_submit_schema,
    _compare_preflight_theory_document_revision,
    _preflight_scratchpad_evidence_errors,
    _search_preflight_sources,
    architect_theory_preflight_workspace_continuation_errors,
    build_architect_theory_execution_preflight_material,
    build_architect_theory_execution_preflight_prompt,
    review_architect_theory_execution_preflight,
    seal_architect_theory_preflight_workspace_checkpoint,
    validate_architect_theory_execution_preflight_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.packet_validation import PacketValidationError
from ai_statistician.evaluation_protocol_revision import (
    architect_metric_requirement_validation_failure_result,
    architect_preexecution_metric_protocol_rejection_result,
)
from ai_statistician.metric_protocol_stage import (
    METRIC_PROTOCOL_PHASE_THEORY_INFORMED_AUTHORING_REQUIRED,
    build_theory_informed_metric_protocol_material,
)
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolTurnResponse,
    GeneratorResponse,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.research_source_library import (
    RESEARCH_SOURCE_READ_TOOL,
    RESEARCH_SOURCE_SEARCH_TOOL,
    ResearchSourceDocument,
    ResearchSourceSnapshot,
)
from ai_statistician.research_source_discovery import (
    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE,
    RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
)
from ai_statistician.scientific_sandbox import ScientificSandboxExecution
from ai_statistician.theory_workspace import (
    THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    THEORY_SCRATCHPAD_TOOL,
    THEORY_MODEL_REASONING_CONTRACT,
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    THEORY_WORKSPACE_HANDOFF_ROLE,
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    TheoryScratchpadConfig,
    read_theory_scratch_execution,
    theory_workspace_document_manifest,
)
from ai_statistician.theory_revision_lineage import (
    build_theory_claim_revision_delta,
)


_TEST_PREFLIGHT_WORKSPACES: list[tempfile.TemporaryDirectory[str]] = []
_DEFAULT_PREFLIGHT_WORKSPACE = tempfile.TemporaryDirectory(
    prefix="preflight-review-default-"
)
_TEST_PREFLIGHT_WORKSPACES.append(_DEFAULT_PREFLIGHT_WORKSPACE)
_DEFAULT_THEORY_WORKSPACE_ROOT = (
    Path(_DEFAULT_PREFLIGHT_WORKSPACE.name)
    / "run"
    / "theory_workspaces"
    / "workspace"
)
_DEFAULT_THEORY_WORKSPACE_ROOT.mkdir(parents=True)


TEST_HAIKU_MODEL = "claude-haiku-4-5-20251001"
PREFLIGHT_CLIENT_TOOL_NAMES = [
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    "search_preflight_sources",
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL,
    "submit_theory_preflight_review",
]


def test_preflight_prompt_requires_independent_mathematical_check() -> None:
    prompt = ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT
    normalized_prompt = " ".join(prompt.split())
    protocol = " ".join(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL)

    assert "exact frozen research question" in normalized_prompt
    assert "authoritative Markdown or LaTeX" in normalized_prompt
    assert "model-selected document, source, and scratch tools" in normalized_prompt
    assert "active candidate text" in normalized_prompt
    assert "every discrete blocker first" in normalized_prompt
    assert "without praise or a verification essay" in normalized_prompt
    assert "never silently repair the candidate" in normalized_prompt
    assert "untrusted observations" in normalized_prompt
    assert protocol.count(THEORY_MODEL_REASONING_CONTRACT) == 1
    assert "exact definitions and stated assumptions" in protocol
    assert "each tool call encodes the proposition" in protocol
    assert "correct conclusion does not validate" in protocol
    assert "your own proposed blockers" in protocol
    assert "report uncertainty rather than inventing" in protocol
    assert "READY_FOR_EXPLORATORY_EXECUTION asks only" in protocol
    assert "Proof or asymptotic disagreement alone does not block READY" in protocol
    assert "BLOCKED requires missing, undefined, contradictory" in protocol
    assert "exploratory" in protocol
    assert "confirmatory" in protocol
    assert "model-owned report owns judgment" in protocol
    assert "citing exact read ranges" in protocol
    assert "do not reproduce the candidate or write a substitute proof" in protocol
    assert len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_SYSTEM_PROMPT) < 1_000
    assert len(protocol) < 3_000
    assert ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL_VERSION == 50


def test_preflight_preserves_the_exact_frozen_research_target() -> None:
    late_obligation = (
        "LATE_PUBLIC_OBLIGATION: distinguish the exact finite statement from its "
        "asymptotic consequence and disclose any unresolved gap."
    )
    description = "A" * 2_400 + " " + late_obligation
    question = OpenResearchQuestion(
        id="long_public_target",
        title="Review every public obligation",
        description=description,
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
        },
    )
    material = build_architect_theory_execution_preflight_material(
        question=question,
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "dimension_requirements": dict(question.task_intent),
        },
    )
    question_anchor = next(
        row for row in material["anchor_catalog"] if row["anchor_id"] == "question"
    )
    prompt = build_architect_theory_execution_preflight_prompt(material)
    prompt_payload = json.loads(prompt.split("\n\n", 1)[1])

    assert question_anchor["content"]["description"] == description
    assert question_anchor["content"]["task_intent"] == question.task_intent
    assert prompt_payload["source_material"]["research_question"] == (
        question_anchor["content"]
    )
    assert late_obligation in prompt


def test_preflight_referee_can_compare_exact_parent_revision_without_treating_diff_as_authority(
    tmp_path: Path,
) -> None:
    parent_text = (
        "# Candidate derivation\n"
        "\n"
        "Claim C1 uses the parent-only unsupported step.\n"
        "The finite procedure returns a typed result.\n"
    )
    revised_text = (
        "# Candidate derivation\n"
        "\n"
        "Claim C1 now derives the step from the stated finite definition.\n"
        "The finite procedure returns a typed result.\n"
    )
    parent_root = tmp_path / "parent"
    revised_root = tmp_path / "revised"
    parent_root.mkdir()
    revised_root.mkdir()
    (parent_root / "theory.md").write_text(parent_text, encoding="utf-8")
    (revised_root / "theory.md").write_text(revised_text, encoding="utf-8")

    claim_index = [
        {
            "id": "C1",
            "kind": "theorem",
            "status": "OPEN",
            "document_path": "theory.md",
            "anchor": "Claim C1",
            "depends_on": [],
        }
    ]
    base_semantic = deepcopy(_theory_material()["theory_semantic_material"])
    assert isinstance(base_semantic, dict)
    base_semantic["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
    base_semantic["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    base_semantic["theory_derivation_packet"]["claim_index"] = claim_index
    parent_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:parent-revision",
        "question": {"id": _question().id},
        **deepcopy(base_semantic),
        "theory_workspace_manifest": theory_workspace_document_manifest(
            {"theory.md": parent_text}, workspace_dir=parent_root
        ),
    }
    revised_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:current-revision",
        "question": {"id": _question().id},
        **deepcopy(base_semantic),
        "theory_workspace_manifest": theory_workspace_document_manifest(
            {"theory.md": revised_text}, workspace_dir=revised_root
        ),
    }
    delta = build_theory_claim_revision_delta(
        parent_theory_packet=parent_packet,
        revised_theory_packet=revised_packet,
    )
    theory_material = build_theory_informed_metric_protocol_material(
        theory_packet=revised_packet,
        theory_packet_id=revised_packet["packet_id"],
        theory_claim_revision_delta=delta,
    )
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=theory_material,
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    prompt = build_architect_theory_execution_preflight_prompt(material)
    observation, inspection_ref = _compare_preflight_theory_document_revision(
        material=material,
        path="theory.md",
        context_lines=1,
    )

    assert "parent-only unsupported step" not in json.dumps(material)
    assert "parent-only unsupported step" not in prompt
    assert "available_theory_document_revisions" in prompt
    assert "-Claim C1 uses the parent-only unsupported step." in observation[
        "unified_diff"
    ]
    assert "+Claim C1 now derives the step" in observation["unified_diff"]
    assert observation["navigation_only"] is True
    assert observation["current_document_read_still_required"] is True
    assert inspection_ref["proof_evidence_status"] == (
        "THEORY_DOCUMENT_REVISION_COMPARISON_NOT_PROOF_EVIDENCE"
    )

    class RevisionReviewBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.diff_observation = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "compare-parent-current",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_COMPARE_REVISION_TOOL,
                        {"path": "theory.md", "context_lines": 1},
                    )
                )
            if turn == 2:
                self.diff_observation = _last_tool_result(request)
                return _tool_response(
                    ClientToolCall(
                        "read-current-candidate",
                        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                        {"path": "theory.md", "line_start": 1, "line_end": 4},
                    )
                )
            return _tool_response(
                ClientToolCall(
                    "submit-after-current-audit",
                    "submit_theory_preflight_review",
                    _compact_submission(_payload(accept=True)),
                )
            )

    backend = RevisionReviewBackend()
    packet = _tool_review(
        backend,
        theory_protocol_material=theory_material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert backend.diff_observation["navigation_only"] is True
    assert [tool.name for tool in backend.requests[0].tools][:3] == [
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_COMPARE_REVISION_TOOL,
    ]
    assert [
        row["tool"] for row in packet["theory_document_inspection_refs"]
    ] == [
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_COMPARE_REVISION_TOOL,
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    ]
    tampered = deepcopy(packet)
    tampered["theory_document_inspection_refs"][0]["diff_sha256"] = "0" * 64
    assert "revision diff mismatch" in " ".join(
        validate_architect_theory_execution_preflight_packet(
            tampered,
            material=material,
        )
    )


def test_source_acceptance_protocol_materializes_one_stable_boolean_abi() -> None:
    materialized, errors = _materialize_source_acceptance_protocol(
        {
            "required_runtime_replicates": 2_000,
            "evaluator_id": "generic-confirmatory-acceptance",
            "acceptance_protocol": (
                "Compute raw bias and coverage diagnostics across the declared "
                "scenarios, retain every check, and accept only when their joint "
                "pre-outcome criterion passes."
            ),
            "scientific_rationale": (
                "Two thousand replicates target the declared Monte Carlo precision."
            ),
        },
        theory_anchor_id="theory_artifact:generic",
    )

    assert errors == []
    assert materialized["requirement_id"] == "generic-confirmatory-acceptance"
    assert materialized["metric_value_kind"] == "boolean"
    assert materialized["operator"] == "=="
    assert materialized["aggregation"] == "identity"
    assert materialized["threshold"] == 1
    assert materialized["gate_field_authorities"] == []
    assert materialized["source_anchors"] == ["theory_artifact:generic"]
    assert materialized["evaluator_mode"] == "simulation_source_acceptance_v1"


class _Backend:
    provider_name = "anthropic"

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests = []

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        return _tool_response(
            ClientToolCall(
                "submit-review",
                "submit_theory_preflight_review",
                _compact_submission(self.payload),
            )
        )

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


class _ScratchPreflightBackend:
    provider_name = "anthropic"

    def __init__(self) -> None:
        self.requests = []
        self.scratch_observation = {}

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        if len(self.requests) <= 4:
            return _tool_response(
                ClientToolCall(
                    f"run-referee-counterexample-{len(self.requests)}",
                    THEORY_SCRATCHPAD_TOOL,
                    {
                        "language": "python",
                        "dependencies": ["numpy"],
                        "code": "print({'counterexample_gap': 0.25, 'seed': seed})\n",
                    },
                )
            )
        self.scratch_observation = _last_tool_result(request)
        return _tool_response(
            ClientToolCall(
                "submit-after-referee-counterexample",
                "submit_theory_preflight_review",
                _compact_submission(_payload(accept=True)),
            )
        )


class _AuthorScratchInspectionBackend:
    provider_name = "anthropic"

    def __init__(self) -> None:
        self.requests = []
        self.author_observation = {}

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        if len(self.requests) == 1:
            return _tool_response(
                ClientToolCall(
                    "read-author-scratch",
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_AUTHOR_SCRATCH_TOOL,
                    {"scratch_run": 1},
                )
            )
        self.author_observation = _last_tool_result(request)
        return _tool_response(
            ClientToolCall(
                "submit-after-author-scratch",
                "submit_theory_preflight_review",
                _compact_submission(_payload(accept=True)),
            )
        )


def _tool_response(*calls: ClientToolCall) -> ClientToolTurnResponse:
    expanded_calls: list[ClientToolCall] = []
    for call in calls:
        tool_input = dict(call.input)
        if (
            call.name == "submit_theory_preflight_review"
            and "review_report_markdown" in tool_input
        ):
            report = str(tool_input.pop("review_report_markdown") or "")
            report_sha256 = hashlib.sha256(report.encode("utf-8")).hexdigest()
            expanded_calls.append(
                ClientToolCall(
                    f"{call.call_id}-write-report",
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                    {"content": report},
                )
            )
            tool_input["review_report_sha256"] = report_sha256
            expanded_calls.append(
                ClientToolCall(call.call_id, call.name, tool_input)
            )
            continue
        expanded_calls.append(call)
    calls = tuple(expanded_calls)
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


def _submit_schema(request) -> dict[str, object]:
    return next(
        tool.input_schema
        for tool in request.tools
        if tool.name == "submit_theory_preflight_review"
    )


def _last_tool_result(request) -> dict[str, object]:
    for block in reversed(request.messages[-1].get("content", [])):
        if isinstance(block, dict) and "content" in block:
            return json.loads(block["content"])
    raise AssertionError("expected a client-tool result in the latest model turn")


def _preflight_prompt_payload(request) -> dict[str, object]:
    prompt = str(request.messages[0]["content"])
    return json.loads(prompt.split("\n\n", 1)[0])


class _PreflightToolBackend:
    provider_name = "anthropic"

    def __init__(
        self,
        *,
        accept: bool,
        payload: dict[str, object] | None = None,
        submit_before_search: bool = False,
        submit_unknown_ref_once: bool = False,
        multiple_searches: bool = False,
        source_scope: str = "theory",
        cite_sources: bool = True,
    ) -> None:
        self.accept = accept
        self.payload = deepcopy(payload) if payload is not None else None
        self.submit_before_search = submit_before_search
        self.submit_unknown_ref_once = submit_unknown_ref_once
        self.multiple_searches = multiple_searches
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
        return _compact_submission(payload)

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        turn = len(self.requests)
        if turn == 1 and self.multiple_searches:
            return _tool_response(
                *[
                    ClientToolCall(
                        f"search-{index}",
                        "search_preflight_sources",
                        {
                            "query": f"finite input censored outcome {index}",
                            "source_scope": self.source_scope,
                            "k": 4,
                        },
                    )
                    for index in range(1, 5)
                ]
            )
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
        for result_block in result_blocks:
            if "content" not in result_block:
                continue
            result = json.loads(result_block["content"])
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
        "theory_workspace_manifest": {
            "schema_version": 1,
            "artifact_kind": "TheoryWorkspaceDocumentManifest",
            "workspace_root": str(_DEFAULT_THEORY_WORKSPACE_ROOT),
            "documents": [],
        },
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
                "output_contract": (
                    "Return (T, observed) when the event occurs and "
                    "(input_length, censored) otherwise."
                ),
                "termination_guarantee": (
                    "Return after consuming at most the finite serialized input."
                ),
                "model_authored_execution_notes": {
                    "bounded_outcome": "The censored flag is part of the estimand."
                },
                "sample_size_order": "The ideal procedure has unspecified duration.",
                "estimator_interface_contract": {
                    "request_fields": [
                        {"name": "observations", "binding": "per_replicate_data"}
                    ],
                    "response_fields": [
                        {
                            "name": "T",
                            "meaning": "ideal first-event index",
                            "normalization": (
                                "positive integer or typed censored outcome"
                            ),
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


def _theory_material_without_estimators() -> dict[str, object]:
    material = deepcopy(_theory_material())
    semantic = material["theory_semantic_material"]
    assert isinstance(semantic, dict)
    semantic["estimator_specs"] = []
    semantic["simulation_ademp_spec"] = {}
    material["source_theory_packet_hash"] = stable_hash(semantic)
    return material


def _theory_only_evidence_contract() -> dict[str, object]:
    return {
        "dimension_requirements": {
            "source_replication": "not_applicable",
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
            "novelty": "not_applicable",
            "unresolved_gaps": "required",
        }
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
            for _dimension in range(2)
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


def _compact_submission(payload: dict[str, object]) -> dict[str, object]:
    if "review_report_markdown" in payload:
        return deepcopy(payload)
    rows = [
        *payload.get("claim_reviews", []),
        *payload.get("dimension_reviews", []),
        *payload.get("estimator_execution_checks", []),
        *payload.get("prior_finding_reviews", []),
        *payload.get("findings", []),
    ]
    evidence_refs: list[str] = []
    report_parts: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for value in row.get("evidence_refs", []) or []:
            ref = str(value)
            if ref and ref not in evidence_refs:
                evidence_refs.append(ref)
        for field in (
            "independent_check",
            "audit_rationale",
            "identity_check",
            "boundary_or_counterexample",
            "rationale",
            "summary",
            "observed_behavior",
            "expected_behavior",
        ):
            value = str(row.get(field, "") or "").strip()
            if value:
                report_parts.append(value)
    reported_statuses = [
        str(row.get("status", "") or "").strip().upper()
        for row in [
            *payload.get("claim_reviews", []),
            *payload.get("dimension_reviews", []),
            *payload.get("estimator_execution_checks", []),
        ]
        if isinstance(row, dict)
    ]
    prior_statuses = [
        str(row.get("status", "") or "").strip().upper()
        for row in payload.get("prior_finding_reviews", [])
        if isinstance(row, dict)
    ]
    findings = deepcopy(payload.get("findings", []))
    report = "# Independent theory preflight\n\n" + "\n\n".join(
        report_parts or ["No additional blocker was identified."]
    )
    overall_verdict = (
        "REVISE"
        if findings
        or any(status != "PASS" for status in reported_statuses)
        or any(
            status
            not in {
                "RESOLVED_BY_CURRENT_THEORY",
                "RETRACTED_BY_CURRENT_EVIDENCE",
            }
            for status in prior_statuses
        )
        else "ACCEPT"
    )
    compact: dict[str, object] = {
        "review_report_markdown": report,
        "report_evidence_refs": evidence_refs or ["theory.estimator_specs"],
        "overall_verdict": overall_verdict,
        "execution_handoff_status": payload.get(
            "execution_handoff_status",
            (
                PREFLIGHT_EXECUTION_HANDOFF_READY
                if overall_verdict == "ACCEPT"
                else PREFLIGHT_EXECUTION_HANDOFF_BLOCKED
            ),
        ),
        "findings": findings,
    }
    if "prior_finding_reviews" in payload:
        compact["prior_finding_statuses"] = [
            str(row.get("status", ""))
            for row in payload.get("prior_finding_reviews", [])
            if isinstance(row, dict)
        ]
    return compact


def _hash_bound_submission(
    payload: dict[str, object],
    *,
    report_sha256: str,
    report_content: str,
) -> dict[str, object]:
    compact = _compact_submission(payload)
    compact.pop("review_report_markdown", None)
    compact["review_report_sha256"] = report_sha256
    return compact


def _with_test_review_workspace(
    theory_material: dict[str, object],
) -> dict[str, object]:
    material = deepcopy(theory_material)
    semantic = material["theory_semantic_material"]
    assert isinstance(semantic, dict)
    manifest = semantic.get("theory_workspace_manifest", {})
    if isinstance(manifest, dict) and manifest.get("workspace_root"):
        return material
    temporary = tempfile.TemporaryDirectory(prefix="preflight-review-")
    _TEST_PREFLIGHT_WORKSPACES.append(temporary)
    workspace_root = (
        Path(temporary.name) / "run" / "theory_workspaces" / "workspace"
    )
    workspace_root.mkdir(parents=True)
    semantic["theory_workspace_manifest"] = {
        "schema_version": 1,
        "artifact_kind": "TheoryWorkspaceDocumentManifest",
        "workspace_root": str(workspace_root),
        "documents": [],
    }
    material["source_theory_packet_hash"] = stable_hash(semantic)
    return material


def _review(*, accept: bool):
    backend = _Backend(_payload(accept=accept))
    packet = review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_with_test_review_workspace(_theory_material()),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
    )
    return packet, backend


def _tool_review(
    backend,
    *,
    source_retriever=None,
    research_sources=None,
    research_source_discovery=None,
    prior_finding_ledger=(),
    theory_protocol_material=None,
    upstream_research_contract=None,
    theory_scratchpad=None,
    author_scratch_execution_refs=(),
    recovery_checkpoint=None,
):
    selected_theory_material = (
        theory_protocol_material
        if theory_protocol_material is not None
        else _theory_material()
    )
    return review_architect_theory_execution_preflight(
        provider=backend,
        question=_question(),
        theory_protocol_material=_with_test_review_workspace(
            selected_theory_material
        ),
        upstream_research_contract=(
            upstream_research_contract
            if upstream_research_contract is not None
            else {
                "formal_targets": [],
                "simulation_targets": ["evaluate the declared risk"],
            }
        ),
        model=TEST_HAIKU_MODEL,
        model_tier="haiku",
        max_tokens=7000,
        temperature=0.0,
        provider_name="anthropic",
        source_retriever=source_retriever,
        research_sources=research_sources,
        research_source_discovery=research_source_discovery,
        prior_finding_ledger=prior_finding_ledger,
        theory_scratchpad=theory_scratchpad,
        author_scratch_execution_refs=author_scratch_execution_refs,
        recovery_checkpoint=recovery_checkpoint,
    )


def test_preflight_client_tool_loop_searches_before_grounded_submission() -> None:
    backend = _PreflightToolBackend(accept=False)

    packet = _tool_review(backend)

    assert packet["overall_verdict"] == "REVISE"
    assert packet["source_grounding_required"] is True
    assert packet["source_grounding_transport"] == (
        "client_tool_model_directed_document_and_source_inspection_v19"
    )
    assert packet["preflight_source_search_count"] == 1
    assert packet["client_tool_loop_turns"] == 2
    assert packet["client_tool_loop_tool_calls"] == 3
    assert packet["client_tool_loop_runtime_executed_tool_calls"] == 3
    session_ref = packet["client_tool_session_ref"]
    assert session_ref["artifact_kind"] == "ClientToolWorkspaceSessionRef"
    assert session_ref["message_count"] >= 3
    assert (
        Path(session_ref["root_path"]) / session_ref["relative_path"]
    ).is_file()
    assert packet["resumed_from_client_tool_session_ref"] == {}
    assert packet["client_tool_session_lineage_continued"] is False
    assert backend.requests[0].metadata["client_tool_loop_max_turns"] == 24
    assert backend.requests[0].metadata["client_tool_loop_max_calls"] == 48
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
    assert [tool.name for tool in backend.requests[0].tools] == (
        PREFLIGHT_CLIENT_TOOL_NAMES
    )
    assert backend.requests[0].tools[0].strict is False
    assert backend.requests[0].tools[-1].strict is False
    assert backend.requests[0].metadata["model_tier"] == "haiku"
    assert backend.requests[0].disable_parallel_tool_use is False
    assert all(request.enable_prompt_caching for request in backend.requests)
    first_result = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert first_result["hits"][0]["source_ref"] == "S1H1"


def test_preflight_referee_can_run_model_owned_exploratory_scratch(
    monkeypatch,
    tmp_path,
) -> None:
    captured = {}

    def fake_execute_scientific_sandbox(**kwargs):
        captured.update(kwargs)
        return ScientificSandboxExecution(
            status="EXECUTED",
            language="python",
            execution_profile="scientific_wasm",
            backend="pyodide",
            isolation_provider="test-isolation",
            dependencies=("numpy",),
            execution_attempted=True,
            returncode=0,
            metrics={"counterexample_gap": 0.25, "seed": 29},
            errors=(),
            stdout_summary="referee scratch stdout",
            stderr_summary="",
            result_parse_error="",
            code_path=str(tmp_path / "scratch.py"),
            request_path=str(tmp_path / "request.json"),
            result_path=str(tmp_path / "result.json"),
            code_hash=stable_hash(kwargs["code"]),
            request_hash="referee-scratch-request-hash",
            result_hash=stable_hash({"counterexample_gap": 0.25, "seed": 29}),
            subprocess_environment_keys=("HOME", "PATH"),
            resource_limits={"cpu_seconds": 11},
        )

    monkeypatch.setattr(
        "ai_statistician.theory_workspace.execute_scientific_sandbox",
        fake_execute_scientific_sandbox,
    )
    backend = _ScratchPreflightBackend()

    packet = _tool_review(
        backend,
        theory_scratchpad=TheoryScratchpadConfig(
            sandbox_dir=tmp_path / "referee-scratch",
            seed=29,
            replicates=17,
            timeout_s=11,
        ),
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["preflight_scratchpad_enabled"] is True
    assert packet["preflight_scratch_runs"] == 4
    assert len(packet["preflight_scratch_execution_refs"]) == 4
    scratch_ref = packet["preflight_scratch_execution_refs"][0]
    assert scratch_ref["proof_evidence_status"] == (
        THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE
    )
    assert scratch_ref["runtime_edited_source"] is False
    assert scratch_ref["runtime_edited_theory"] is False
    assert packet["preflight_scratch_execution_fingerprint"] == stable_hash(
        packet["preflight_scratch_execution_refs"]
    )
    assert backend.scratch_observation["metrics"] == {
        "counterexample_gap": 0.25,
        "seed": 29,
    }
    assert captured["seed"] == 29
    assert captured["replicates"] == 17
    assert captured["timeout_s"] == 11
    assert THEORY_SCRATCHPAD_TOOL in [
        tool.name for tool in backend.requests[0].tools
    ]
    assert packet["client_tool_loop_turns"] == 5
    assert packet["client_tool_loop_tool_calls"] == 6
    assert "client_tool_session_ref" in packet["client_tool_loop_history"][0][
        "tool_calls"
    ][0]["result_excerpt"]
    tampered = deepcopy(packet)
    tampered["preflight_scratch_execution_refs"][0][
        "proof_evidence_status"
    ] = "KERNEL_VERIFIED"
    assert any(
        "proof boundary mismatch" in error
        for error in _preflight_scratchpad_evidence_errors(tampered)
    )


def test_preflight_can_inspect_exact_author_scratch_without_copying_it(
    tmp_path,
) -> None:
    scratch_root = tmp_path / "shared-theory-scratch"
    scratch_root.mkdir()
    source = (
        "AUTHOR_SCRATCH_UNIQUE_MARKER = 41\n"
        "def run_sandbox(seed, replicates):\n"
        "    return {'residual': AUTHOR_SCRATCH_UNIQUE_MARKER - 40}\n"
    )
    result = {"residual": 1, "seed": 29}
    source_path = scratch_root / "author_run.py"
    result_path = scratch_root / "author_result.json"
    source_path.write_text(source, encoding="utf-8")
    result_path.write_text(json.dumps(result), encoding="utf-8")
    author_ref = {
        "scratch_run": 1,
        "status": "EXECUTED",
        "language": "python",
        "execution_attempted": True,
        "returncode": 0,
        "dependencies": ["numpy"],
        "errors": [],
        "code_path": str(source_path),
        "code_hash": stable_hash(source),
        "request_hash": "author-scratch-request-hash",
        "result_path": str(result_path),
        "result_hash": stable_hash(result),
        "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    }
    backend = _AuthorScratchInspectionBackend()

    packet = _tool_review(
        backend,
        theory_scratchpad=TheoryScratchpadConfig(
            sandbox_dir=scratch_root,
            seed=29,
            replicates=17,
        ),
        author_scratch_execution_refs=(author_ref,),
    )

    assert backend.author_observation["source"] == source
    assert backend.author_observation["result"] == result
    assert "does not validate" in backend.author_observation["boundary"]
    assert ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_AUTHOR_SCRATCH_TOOL in [
        tool.name for tool in backend.requests[0].tools
    ]
    inspection_ref = backend.author_observation["inspection_ref"]
    assert inspection_ref["code_hash"] == stable_hash(source)
    assert inspection_ref["result_hash"] == stable_hash(result)
    assert inspection_ref["proof_evidence_status"] == (
        THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE
    )
    assert "AUTHOR_SCRATCH_UNIQUE_MARKER" not in json.dumps(packet)
    initial_prompt = json.dumps(_preflight_prompt_payload(backend.requests[0]))
    assert "code_path" not in initial_prompt
    assert "result_path" not in initial_prompt


def test_author_scratch_inspection_rejects_stale_or_unbound_files(tmp_path) -> None:
    scratch_root = tmp_path / "scratch-root"
    scratch_root.mkdir()
    source = "def run_sandbox(seed, replicates):\n    return {'value': 1}\n"
    source_path = scratch_root / "author.py"
    source_path.write_text(source, encoding="utf-8")
    base_ref = {
        "scratch_run": 1,
        "code_path": str(source_path),
        "code_hash": stable_hash(source),
        "request_hash": "request-hash",
        "proof_evidence_status": THEORY_SCRATCHPAD_NOT_PROOF_EVIDENCE,
    }

    with pytest.raises(ClientToolInputError, match="source hash is stale"):
        read_theory_scratch_execution(
            ref={**base_ref, "code_hash": "stale"},
            scratch_root=scratch_root,
        )

    outside_path = tmp_path / "outside.py"
    outside_path.write_text(source, encoding="utf-8")
    with pytest.raises(ClientToolInputError, match="outside its sandbox"):
        read_theory_scratch_execution(
            ref={**base_ref, "code_path": str(outside_path)},
            scratch_root=scratch_root,
        )


def test_preflight_failed_scratch_keeps_model_request_identity(
    monkeypatch,
    tmp_path,
) -> None:
    def fake_execute_scientific_sandbox(**kwargs):
        return ScientificSandboxExecution(
            status="REJECTED_CONTRACT",
            language="python",
            execution_profile="scientific_wasm",
            backend="pyodide",
            isolation_provider="test-isolation",
            dependencies=("numpy",),
            execution_attempted=False,
            returncode=-1,
            metrics={},
            errors=("model-authored source violates the sandbox ABI",),
            stdout_summary="",
            stderr_summary="model-authored source violates the sandbox ABI",
            result_parse_error="",
            code_path="",
            request_path="",
            result_path="",
            code_hash=stable_hash(kwargs["code"]),
            request_hash="",
            result_hash="",
            subprocess_environment_keys=("HOME", "PATH"),
            resource_limits={"cpu_seconds": 11},
        )

    monkeypatch.setattr(
        "ai_statistician.theory_workspace.execute_scientific_sandbox",
        fake_execute_scientific_sandbox,
    )
    backend = _ScratchPreflightBackend()

    packet = _tool_review(
        backend,
        theory_scratchpad=TheoryScratchpadConfig(
            sandbox_dir=tmp_path / "referee-scratch",
            seed=29,
            replicates=17,
            timeout_s=11,
        ),
    )

    assert packet["overall_verdict"] == "ACCEPT"
    scratch_refs = packet["preflight_scratch_execution_refs"]
    assert len(scratch_refs) == 4
    assert all(ref["status"] == "REJECTED_CONTRACT" for ref in scratch_refs)
    assert all(ref["execution_attempted"] is False for ref in scratch_refs)
    assert all(ref["request_hash"] for ref in scratch_refs)
    scratch_ref = scratch_refs[-1]
    assert scratch_ref["request_identity_source"] == "model_tool_request"
    assert backend.scratch_observation["request_hash"] == scratch_ref["request_hash"]
    assert backend.scratch_observation["request_identity_source"] == (
        "model_tool_request"
    )
    assert _preflight_scratchpad_evidence_errors(packet) == []
    assert "never describe a rejected or failed run as passed" in " ".join(
        backend.requests[0].system_prompt.split()
    )
    assert "model-authored discriminating checks" in (
        backend.requests[0].messages[0]["content"]
    )
    scratch_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == THEORY_SCRATCHPAD_TOOL
    )
    assert "ordinary script" in scratch_tool.description
    assert "entrypoint" not in scratch_tool.input_schema["properties"]
    assert "execution_profile" not in scratch_tool.input_schema["properties"]
    assert "validates only this submitted program" in scratch_tool.description
    assert "joint dependence" in scratch_tool.description


def test_preflight_allows_model_selected_searches_under_shared_tool_budget() -> None:
    backend = _PreflightToolBackend(
        accept=False,
        multiple_searches=True,
    )

    packet = _tool_review(backend)

    assert packet["preflight_source_search_count"] == 4
    assert "preflight_source_search_budget" not in packet
    assert len(backend.requests) == 2
    expected_tools = {
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        "search_preflight_sources",
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL,
        "submit_theory_preflight_review",
    }
    assert all(
        {tool.name for tool in request.tools} == expected_tools
        for request in backend.requests
    )
    assert all(request.enable_prompt_caching for request in backend.requests)


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
    assert "source_evidence_refs" not in continued
    assert any(
        hit.get("source_hit_id") == backend.hit_id
        for observation in packet["preflight_source_observations"]
        for hit in observation.get("hits", [])
    )
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


def test_preflight_formal_not_applicable_excludes_formal_sources() -> None:
    class ForbiddenFormalRetriever:
        def __init__(self) -> None:
            self.calls = 0

        def search(self, query, *, k):
            self.calls += 1
            raise AssertionError("formal retriever must not run")

    theory_material = _theory_material()
    theory_material["retrieval_context"] = {
        "formal_source_hits": [
            {
                "hits": [
                    {
                        "source_id": "statlib",
                        "path": "Statlib/Hidden.lean",
                        "name": "Statlib.hidden",
                        "signature": "hidden_statement",
                    }
                ]
            }
        ]
    }
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=theory_material,
        upstream_research_contract={
            "dimension_requirements": {"formal": "not_applicable"},
        },
    )
    retriever = ForbiddenFormalRetriever()

    observation = _search_preflight_sources(
        material=material,
        source_retriever=retriever,
        query="finite observation procedure",
        source_scope="all",
        k=8,
        search_index=1,
    )

    assert material["formal_sources_applicable"] is False
    assert retriever.calls == 0
    assert all(
        hit["source_kind"] != "formal_library_declaration"
        for hit in observation["hits"]
    )
    with pytest.raises(ClientToolInputError):
        _search_preflight_sources(
            material=material,
            source_retriever=retriever,
            query="hidden formal declaration",
            source_scope="formal_library",
            k=4,
            search_index=2,
        )


def test_preflight_reviewer_can_search_and_read_task_bound_research_source(
    tmp_path: Path,
) -> None:
    theory_text = (
        "# Candidate theory\n"
        "\n"
        "The finite procedure returns a typed outcome on every admitted input.\n"
    )
    theory_path = tmp_path / "candidate_theory.md"
    theory_path.write_text(theory_text, encoding="utf-8")
    theory_material = _theory_material()
    semantic_material = theory_material["theory_semantic_material"]
    semantic_material["theory_workspace_manifest"] = (
        theory_workspace_document_manifest(
            {"candidate_theory.md": theory_text},
            workspace_dir=tmp_path,
        )
    )
    semantic_material["theory_content_authority"] = (
        THEORY_WORKSPACE_CONTENT_AUTHORITY
    )
    semantic_material["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    source_text = (
        "# Exact finite-sample result\n"
        "\n"
        "Under independent Gaussian sampling, the pivotal ratio has a Student "
        "distribution with n minus one degrees of freedom.\n"
        "Inverting its two-sided quantiles gives the stated confidence interval.\n"
    )
    source_path = tmp_path / "student.md"
    source_path.write_text(source_text, encoding="utf-8")
    manifest_path = tmp_path / "sources.json"
    manifest_path.write_text("{}", encoding="utf-8")
    source_sha256 = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    snapshot = ResearchSourceSnapshot(
        snapshot_id="student-source",
        source_horizon="1908-12-31",
        snapshot_hash=stable_hash(["student-source", source_sha256]),
        manifest_sha256=hashlib.sha256(b"{}").hexdigest(),
        documents=(
            ResearchSourceDocument(
                document_id="student-paper",
                title="Exact finite-sample result",
                source_kind="paper",
                relative_path="student.md",
                sha256=source_sha256,
                citation="Student (1908)",
                lines=tuple(source_text.splitlines()),
            ),
        ),
        manifest_path=manifest_path,
        source_root=tmp_path,
    )

    class ResearchSourceBackend(_PreflightToolBackend):
        def __init__(self) -> None:
            super().__init__(accept=False)
            self.read_hit_id = ""

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-independent-reconstruction",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {
                            "content": (
                                "# Independent reconstruction\n\nThe question and "
                                "contract require a finite total procedure; the "
                                "candidate derivation has not been inspected.\n"
                            )
                        },
                    )
                )
            if turn == 2:
                return _tool_response(
                    ClientToolCall(
                        "read-theory-document",
                        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                        {
                            "path": "candidate_theory.md",
                            "line_start": 1,
                            "line_end": 3,
                        },
                    )
                )
            if turn == 3:
                return _tool_response(
                    ClientToolCall(
                        "search-research-source",
                        RESEARCH_SOURCE_SEARCH_TOOL,
                        {
                            "query": "pivotal ratio degrees freedom",
                            "top_k": 2,
                        },
                    )
                )
            result = json.loads(request.messages[-1]["content"][0]["content"])
            if turn == 4:
                hit = result["hits"][0]
                return _tool_response(
                    ClientToolCall(
                        "read-research-source",
                        RESEARCH_SOURCE_READ_TOOL,
                        {
                            "document_id": hit["document_id"],
                            "line_start": hit["line_start"],
                            "line_end": hit["line_end"],
                        },
                    )
                )
            self.read_hit_id = result["source_hit_id"]
            return _tool_response(
                ClientToolCall(
                    "submit-source-grounded-review",
                    "submit_theory_preflight_review",
                    self._submission(source_ref=result["source_ref"]),
                )
            )

    backend = ResearchSourceBackend()
    packet = _tool_review(
        backend,
        research_sources=snapshot,
        theory_protocol_material=theory_material,
        upstream_research_contract={
            "dimension_requirements": {"formal": "not_applicable"},
            "simulation_targets": ["evaluate the declared risk"],
        },
    )

    assert [tool.name for tool in backend.requests[0].tools] == [
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        RESEARCH_SOURCE_SEARCH_TOOL,
        RESEARCH_SOURCE_READ_TOOL,
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL,
        "submit_theory_preflight_review",
    ]
    assert "search_preflight_sources" not in backend.requests[0].messages[0][
        "content"
    ]
    assert backend.requests[0].tools[-1].strict is False
    submit_schema = backend.requests[0].tools[-1].input_schema
    assert submit_schema["properties"]["overall_verdict"]["enum"] == [
        "ACCEPT",
        "REVISE",
    ]
    assert "dimension_statuses" not in submit_schema["properties"]
    assert submit_schema["properties"]["review_report_sha256"]["type"] == (
        "string"
    )
    assert "review_report_markdown" not in submit_schema["properties"]
    assert packet["preflight_source_search_count"] == 1
    assert [
        row["source_scope"]
        for row in packet["preflight_source_observations"]
    ] == ["research_sources", "research_source_read"]
    assert [
        row["hits"][0]["source_kind"]
        for row in packet["preflight_source_observations"]
    ] == [
        "research_source_search_passage",
        "research_source_exact_passage",
    ]
    assert packet["findings"][0]["source_evidence_refs"] == [
        backend.read_hit_id
    ]
    assert all(
        "excerpt" not in hit and "content" in hit
        for observation in packet["preflight_source_observations"]
        for hit in observation["hits"]
    )
    assert (
        "Inverting its two-sided quantiles gives the stated confidence interval."
        not in json.dumps(packet)
    )
    assert all(
        "client_tool_session_ref" in call["result_excerpt"]
        for turn in packet["client_tool_loop_history"]
        for call in turn["tool_calls"]
        if not call["is_error"]
        if call["name"]
        in {RESEARCH_SOURCE_SEARCH_TOOL, RESEARCH_SOURCE_READ_TOOL}
    )


def test_preflight_referee_independently_discovers_reads_and_cites_public_source() -> None:
    source_body = (
        "# Contrary finite-sample result\n\n"
        "The displayed normalization fails when the support contains a boundary atom."
    )
    source_hash = hashlib.sha256(source_body.encode("utf-8")).hexdigest()

    class PublicSourceDiscovery:
        def __init__(self) -> None:
            self.search_calls = []
            self.read_calls = []

        def descriptor(self):
            return {
                "schema_version": 1,
                "provider": "test_crossref",
                "source_horizon": "2025-12-31",
                "model_selects_queries": True,
                "model_selects_sources": True,
                "proof_evidence_status": (
                    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
                ),
            }

        def search(self, query, *, source_kind="all", top_k=5):
            self.search_calls.append((query, source_kind, top_k))
            return {
                "ok": True,
                "provider": "test_crossref",
                "source_horizon": "2025-12-31",
                "query": query,
                "query_hash": stable_hash(query),
                "source_kind": source_kind,
                "results": [
                    {
                        "source_handle": "public-source:opaque",
                        "source_kind": "paper",
                        "title": "Contrary finite-sample result",
                        "url": "https://doi.org/10.0000/example",
                        "publication_date": "2024-06-01",
                        "citation": "Example (2024)",
                        "summary": "A possible boundary-case conflict.",
                    }
                ],
                "proof_evidence_status": (
                    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
                ),
            }

        def read(self, source_handle, *, path="", revision=""):
            self.read_calls.append((source_handle, path, revision))
            return {
                "ok": True,
                "provider": "test_crossref",
                "source_handle": source_handle,
                "source_kind": "paper",
                "title": "Contrary finite-sample result",
                "url": "https://doi.org/10.0000/example",
                "publication_date": "2024-06-01",
                "citation": "Example (2024)",
                "revision": "crossref-record:immutable",
                "path": "metadata.md",
                "content": source_body,
                "content_sha256": source_hash,
                "content_truncated": False,
                "citation_ref": "public-research-source-ref:immutable",
                "proof_evidence_status": (
                    RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
                ),
            }

    class PublicSourceBackend(_PreflightToolBackend):
        def __init__(self) -> None:
            super().__init__(accept=False)
            self.search_result = {}
            self.read_result = {}
            self.read_hit_id = ""

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "discover-independent-source",
                        RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
                        {
                            "query": "finite support boundary normalization",
                            "source_kind": "paper",
                            "top_k": 3,
                        },
                    )
                )
            result = _last_tool_result(request)
            if turn == 2:
                self.search_result = result
                return _tool_response(
                    ClientToolCall(
                        "read-independent-source",
                        RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
                        {
                            "source_handle": result["results"][0][
                                "source_handle"
                            ]
                        },
                    )
                )
            self.read_result = result
            self.read_hit_id = str(result["source_hit_id"])
            return _tool_response(
                ClientToolCall(
                    "submit-independent-source-review",
                    "submit_theory_preflight_review",
                    self._submission(source_ref=str(result["source_ref"])),
                )
            )

    discovery = PublicSourceDiscovery()
    backend = PublicSourceBackend()
    packet = _tool_review(
        backend,
        research_source_discovery=discovery,
    )

    tool_names = [tool.name for tool in backend.requests[0].tools]
    assert RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL in tool_names
    assert RESEARCH_SOURCE_DISCOVERY_READ_TOOL in tool_names
    assert discovery.search_calls == [
        ("finite support boundary normalization", "paper", 3)
    ]
    assert discovery.read_calls == [("public-source:opaque", "", "")]
    assert all(
        "source_ref" not in result
        for result in backend.search_result["results"]
    )
    assert backend.read_result["source_ref"] == "S2H1"
    assert packet["preflight_public_research_source_search_count"] == 1
    assert packet["preflight_public_research_source_read_count"] == 1
    assert packet["preflight_public_research_source_discovery"][
        "source_horizon"
    ] == "2025-12-31"
    assert len(packet["preflight_source_observations"]) == 1
    observation = packet["preflight_source_observations"][0]
    assert observation["source_scope"] == "public_research_source_read"
    hit = observation["hits"][0]
    assert hit["source_kind"] == "public_research_source_exact_read"
    assert hit["content"]["content_sha256"] == source_hash
    assert hit["content"]["observed_content_sha256"] == source_hash
    assert packet["findings"][0]["source_evidence_refs"] == [
        backend.read_hit_id
    ]
    assert source_body not in json.dumps(packet)
    public_history_calls = [
        call
        for turn in packet["client_tool_loop_history"]
        for call in turn["tool_calls"]
        if call["name"]
        in {
            RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
            RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
        }
    ]
    assert len(public_history_calls) == 2
    assert all(
        "client_tool_session_ref" in call["result_excerpt"]
        for call in public_history_calls
    )


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
    theory_material = _theory_material()
    theory_material["retrieval_context"] = {
        "knowledge_cards": [
            {
                "id": "finite_input_reference",
                "title": "Finite input and censored outcomes",
                "summary": (
                    "A finite input censored outcome remains typed and observable."
                ),
            }
        ]
    }

    packet = _tool_review(
        backend,
        source_retriever=FormalRetriever(),
        theory_protocol_material=theory_material,
    )

    hits = packet["preflight_source_observations"][0]["hits"]
    assert {hit["retrieval_channel"] for hit in hits} == {
        "theory",
        "retrieval_memory",
        "formal_library",
    }
    assert [hit["retrieval_channel"] for hit in hits[:3]] == [
        "theory",
        "retrieval_memory",
        "formal_library",
    ]
    assert packet["preflight_source_observations"][0]["retrieval_fusion"] == (
        "round_robin_theory_retrieval_formal_v3_cross_turn_deduplicated"
    )
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
    failed_submit = next(
        row
        for row in packet["client_tool_loop_history"][1]["tool_calls"]
        if row["name"] == "submit_theory_preflight_review"
    )
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
            result = _last_tool_result(request)
            if result.get("hits"):
                self.hit_id = result["hits"][0]["source_hit_id"]
                self.source_ref = result["hits"][0]["source_ref"]
            if turn == 2:
                payload = _payload(accept=True)
                payload["findings"] = deepcopy(_payload(accept=False)["findings"])
                payload["findings"][0]["source_evidence_refs"] = [self.source_ref]
                submission = _compact_submission(payload)
                submission["overall_verdict"] = "ACCEPT"
                return _tool_response(
                    ClientToolCall(
                        "submit-inconsistent",
                        "submit_theory_preflight_review",
                        submission,
                    )
                )
            assert result["error"] == "preflight_submission_rejected"
            assert any(
                "overall verdict contradicts" in error
                for error in result["validation_errors"]
            )
            return _tool_response(
                ClientToolCall(
                    "submit-consistent",
                    "submit_theory_preflight_review",
                    _compact_submission(_payload(accept=True)),
                )
            )

    backend = AllPassFindingBackend(accept=True)

    packet = _tool_review(backend)

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["findings"] == []
    assert len(backend.requests) == 3
    assert {request.model for request in backend.requests} == {TEST_HAIKU_MODEL}
    rejected = next(
        row
        for row in packet["client_tool_loop_history"][1]["tool_calls"]
        if row["name"] == "submit_theory_preflight_review"
    )
    assert rejected["name"] == "submit_theory_preflight_review"
    assert rejected["is_error"] is True
    assert "overall verdict contradicts" in rejected["result_excerpt"]


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
            result = _last_tool_result(request)
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
    rejected = next(
        row
        for row in packet["client_tool_loop_history"][1]["tool_calls"]
        if row["name"] == "submit_theory_preflight_review"
    )
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
    assert [tool.name for tool in backend.requests[3].tools] == (
        PREFLIGHT_CLIENT_TOOL_NAMES
    )
    assert [tool.name for tool in backend.requests[4].tools] == (
        PREFLIGHT_CLIENT_TOOL_NAMES
    )
    assert "client_tool_loop_max_terminal_recovery_turns" not in (
        backend.requests[4].metadata
    )
    failed_submit = next(
        row
        for row in packet["client_tool_loop_history"][3]["tool_calls"]
        if row["name"] == "submit_theory_preflight_review"
    )
    assert failed_submit["is_error"] is True
    assert packet["client_tool_loop_turns"] == 5


def test_preflight_client_tool_loop_allows_model_to_submit_without_search() -> None:
    backend = _PreflightToolBackend(
        accept=False,
        submit_before_search=True,
    )

    packet = _tool_review(backend)

    assert len(backend.requests) == 1
    first_submit = next(
        row
        for row in packet["client_tool_loop_history"][0]["tool_calls"]
        if row["name"] == "submit_theory_preflight_review"
    )
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

    assert len(backend.requests) == 1
    assert [tool.name for tool in backend.requests[0].tools] == (
        PREFLIGHT_CLIENT_TOOL_NAMES
    )
    assert "client_tool_loop_terminal_decision_reason" not in (
        backend.requests[-1].metadata
    )
    assert "model ended the workspace turn without a client tool call" in str(
        exc_info.value
    )


def test_preflight_referee_resumes_exact_tool_workspace_across_outer_steps(
    tmp_path,
) -> None:
    document = (
        "# Candidate derivation\n"
        "Define a finite observation and its target risk.\n"
        "The central identity follows by conditioning on the observed branch.\n"
        "A boundary case remains available for independent inspection.\n"
    )
    workspace = tmp_path / "theory-workspace"
    document_path = workspace / "theory" / "workspace.md"
    document_path.parent.mkdir(parents=True)
    document_path.write_text(document, encoding="utf-8")
    material = _theory_material()
    semantic = material["theory_semantic_material"]
    assert isinstance(semantic, dict)
    semantic["theory_workspace_manifest"] = theory_workspace_document_manifest(
        {"theory/workspace.md": document},
        workspace_dir=workspace,
    )
    material["source_theory_packet_hash"] = stable_hash(semantic)

    class FirstSegmentBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-independent-reconstruction",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {
                            "content": (
                                "# Independent reconstruction\n\nThe finite target must "
                                "be derived without assuming the candidate's "
                                "conditioning argument.\n"
                            )
                        },
                    )
                )
            if turn == 2:
                return _tool_response(
                    ClientToolCall(
                        "read-authoritative-derivation",
                        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                        {
                            "path": "theory/workspace.md",
                            "line_start": 1,
                            "line_end": 4,
                        },
                    )
                )
            if turn == 3:
                return _tool_response(
                    ClientToolCall(
                        "search-task-bound-source",
                        "search_preflight_sources",
                        {
                            "query": "finite observation target risk",
                            "source_scope": "theory",
                            "k": 2,
                        },
                    )
                )
            if 4 <= turn <= 11:
                return _tool_response(
                    ClientToolCall(
                        f"inspect-later-range-{turn}",
                        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
                        {"query": f"recent checkpoint observation {turn - 4}"},
                    )
                )
            if turn == 12:
                invalid = _compact_submission(_payload(accept=False))
                invalid["overall_verdict"] = "ACCEPT"
                return _tool_response(
                    ClientToolCall(
                        "submit-structurally-incomplete-review",
                        "submit_theory_preflight_review",
                        invalid,
                    )
                )
            return _tool_response()

    first_backend = FirstSegmentBackend()
    with pytest.raises(PacketValidationError) as first_error:
        _tool_review(
            first_backend,
            theory_protocol_material=material,
        )

    checkpoint = first_error.value.recovery_checkpoint
    assert checkpoint["artifact_kind"] == (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WORKSPACE_CHECKPOINT_KIND
    )
    assert checkpoint["resumable"] is True
    assert checkpoint["runtime_selected_review_semantics"] is False
    assert checkpoint["implementation_authorized"] is False
    assert checkpoint["kernel_verified"] is False
    assert checkpoint["searches"] == 1
    assert checkpoint["theory_document_inspection_refs"][0]["line_end"] == 4
    session_ref = checkpoint["client_tool_session_ref"]
    assert session_ref["artifact_kind"] == "ClientToolWorkspaceSessionRef"
    assert (
        Path(session_ref["root_path"]) / session_ref["relative_path"]
    ).is_file()
    report_draft = checkpoint["review_report_draft"]
    assert set(report_draft) == {
        "schema_version",
        "artifact_kind",
        "content_authority",
        "media_type",
        "relative_path",
        "path",
        "sha256",
        "byte_size",
        "version",
        "persisted",
        "proof_evidence_status",
    }
    assert Path(report_draft["path"]).is_file()
    assert "review_report_markdown" not in json.dumps(checkpoint)
    assert any(
        row["tool"] == "submit_theory_preflight_review" and row["is_error"]
        for row in checkpoint["workspace_observations"]
    )
    assert any(
        isinstance(row["content"], dict)
        and row["content"].get("content") == document.strip()
        for row in checkpoint["workspace_observations"]
    )
    source_ref = next(
        iter(checkpoint["source_ref_by_hit_id"].values())
    )

    class SecondSegmentBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            opening = str(request.messages[0]["content"])
            retained_context = json.dumps(request.messages)
            assert checkpoint["checkpoint_id"] in opening
            assert "prior_model_visible_tool_observations" not in opening
            assert "Candidate derivation" not in opening
            assert source_ref not in opening
            assert report_draft["sha256"] in opening
            assert "Candidate derivation" not in retained_context
            assert "recent checkpoint observation 7" in retained_context
            window = request.metadata["client_tool_checkpoint_window"]
            assert window["parent_opening_replayed"] is False
            assert window["prior_transcript_replayed"] is True
            assert window["replayed_tool_rounds"] == 8
            assert window["summary_used"] is False
            return _tool_response(
                ClientToolCall(
                    "submit-from-restored-observations",
                    "submit_theory_preflight_review",
                    _hash_bound_submission(
                        _payload(accept=True),
                        report_sha256=report_draft["sha256"],
                        report_content=Path(report_draft["path"]).read_text(
                            encoding="utf-8"
                        ),
                    ),
                )
            )

    second_backend = SecondSegmentBackend()
    packet = _tool_review(
        second_backend,
        theory_protocol_material=material,
        recovery_checkpoint=checkpoint,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["workspace_resumed_from_model_checkpoint"] is True
    assert packet["workspace_resumed_from_checkpoint_id"] == (
        checkpoint["checkpoint_id"]
    )
    assert packet["resumed_from_client_tool_session_ref"] == session_ref
    assert packet["client_tool_session_lineage_continued"] is True
    assert packet["client_tool_checkpoint_window"][
        "parent_opening_replayed"
    ] is False
    assert packet["client_tool_checkpoint_window"][
        "replayed_tool_rounds"
    ] == 8
    assert packet["client_tool_session_ref"] != session_ref
    assert packet["preflight_source_search_count"] == 1
    assert packet["theory_document_inspection_refs"] == (
        checkpoint["theory_document_inspection_refs"]
    )
    assert packet["client_tool_loop_turns"] == (
        checkpoint["client_tool_loop_turns"] + 1
    )
    assert len(second_backend.requests) == 1


def test_preflight_referee_rejects_tampered_and_stalled_checkpoints() -> None:
    with pytest.raises(PacketValidationError) as first_error:
        class OneObservationThenStop:
            provider_name = "anthropic"

            def __init__(self) -> None:
                self.requests = []

            def generate_client_tool_turn(self, request):
                self.requests.append(request)
                if len(self.requests) == 1:
                    return _tool_response(
                        ClientToolCall(
                            "search-once",
                            "search_preflight_sources",
                            {
                                "query": "finite observation target",
                                "source_scope": "theory",
                                "k": 1,
                            },
                        )
                    )
                return _tool_response()

        _tool_review(OneObservationThenStop())

    checkpoint = first_error.value.recovery_checkpoint
    tampered = deepcopy(checkpoint)
    tampered["searches"] = 0

    class MustNotRun:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            raise AssertionError("tampered checkpoint must fail before model call")

    blocked_backend = MustNotRun()
    with pytest.raises(PacketValidationError, match="checkpoint"):
        _tool_review(blocked_backend, recovery_checkpoint=tampered)
    assert blocked_backend.requests == []

    tampered_session_body = deepcopy(checkpoint)
    tampered_session_body.pop("checkpoint_id")
    tampered_session_body["client_tool_session_ref"]["sha256"] = "0" * 64
    tampered_session = seal_architect_theory_preflight_workspace_checkpoint(
        tampered_session_body
    )
    session_blocked_backend = MustNotRun()
    with pytest.raises(ValueError, match="session bytes"):
        _tool_review(
            session_blocked_backend,
            recovery_checkpoint=tampered_session,
        )
    assert session_blocked_backend.requests == []

    stalled_body = deepcopy(checkpoint)
    stalled_body.pop("checkpoint_id")
    stalled_body["resumed_from_checkpoint_id"] = checkpoint["checkpoint_id"]
    stalled_body["segment_start_observation_count"] = len(
        checkpoint["workspace_observation_fingerprints"]
    )
    stalled_body["segment_start_counters"] = {
        field: checkpoint[field]
        for field in (
            "searches",
            "source_operations",
            "scratch_runs",
            "client_tool_loop_turns",
            "client_tool_loop_tool_calls",
            "client_tool_loop_runtime_executed_tool_calls",
        )
    }
    stalled_body["resumable"] = False
    stalled_body["model_owned_workspace_actions"] = False
    stalled = seal_architect_theory_preflight_workspace_checkpoint(stalled_body)
    errors = architect_theory_preflight_workspace_continuation_errors(
        stalled,
        prior_checkpoint=checkpoint,
    )
    assert "referee workspace continuation added no new observation" in errors
    assert "referee workspace made no new environment-observed progress" in errors


def test_preflight_json_only_transport_is_disabled() -> None:
    class JSONOnlyBackend:
        provider_name = "anthropic"

        def generate(self, request):
            return GeneratorResponse(
                text=json.dumps(_payload(accept=True)),
                provider="anthropic",
                model=request.model,
            )

    with pytest.raises(
        ValueError,
        match="JSON-only mathematical review is disabled",
    ):
        review_architect_theory_execution_preflight(
            provider=JSONOnlyBackend(),
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
        )


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
    assert "the review protocol" in verdict_policy
    assert "material active falsehood" in verdict_policy
    assert "correct endpoint" in verdict_policy
    assert "later correction" in verdict_policy
    assert "exact inspected range" in verdict_policy
    assert "checkable derivation" in verdict_policy
    assert "downstream proof obligations" in verdict_policy
    assert "complete mathematical argument" not in verdict_policy
    packet, backend = _review(accept=True)

    assert len(prompt) < 24_000
    protocol = " ".join(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL)
    for phrase in (
        "structured handoff is only an index",
        "model-directed search and exact range reads",
        "smallest set of load-bearing claims",
        "exact definitions and stated assumptions",
        "deriving both sides from common definitions",
        "each tool call encodes the proposition",
        "correct conclusion does not validate",
        "your own proposed blockers",
        "Scratch and retrieval establish only",
        "Separate mathematical coherence, proof completeness",
        "READY_FOR_EXPLORATORY_EXECUTION asks only",
        "BLOCKED requires missing, undefined, contradictory",
        "one compact finding per blocker",
        "findings-first Markdown review",
        "do not reproduce the candidate or write a substitute proof",
    ):
        assert phrase in protocol
    assert len(ARCHITECT_THEORY_EXECUTION_PREFLIGHT_PROTOCOL) == 5
    assert protocol.count(THEORY_MODEL_REASONING_CONTRACT) == 1
    assert len(protocol) < 3_000
    assert "every discrete blocker" in protocol
    assert "executive summary" in protocol
    assert "section-by-section verification" in protocol
    source_tool_prompt = str(backend.requests[0].messages[0]["content"])
    assert "independent read-only calls may be batched" in source_tool_prompt
    assert "scratch, report mutation, and submission" in source_tool_prompt
    assert "write a replacement proof" in source_tool_prompt
    assert "submit only its current SHA-256" in source_tool_prompt
    assert "strengths, praise" in source_tool_prompt
    assert "Before candidate-document access" not in str(
        backend.requests[0].messages[0]["content"]
    )
    for retired_corner_case in (
        "missing or extra sample-size factor",
        "fixed-candidate result does not automatically survive",
        "not observed within a resource bound",
    ):
        assert retired_corner_case not in protocol
    assert packet["overall_verdict"] == "ACCEPT"
    assert "runtime_estimator_status_normalizations" not in packet
    assert material["execution_handoff_available"] is True
    assert "required_review_components" not in material
    assert packet["review_scope"] == {
        "execution_handoff_required": True,
        "execution_handoff_available": True,
        "formal_sources_applicable": True,
    }
    assert "component_reviews" not in packet
    assert "runtime_estimator_identity_bindings" not in packet
    assert packet["execution_authorized"] is False
    assert packet["kernel_verified"] is False
    assert packet["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")
    anchor_ids = {
        row["anchor_id"] for row in material["anchor_catalog"]
    }
    assert "theory.rejected_alternatives" in anchor_ids
    assert "theory.sanity_checks" not in anchor_ids
    assert "theory.sanity_check_index" not in anchor_ids
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
            }
        ],
        "declared_output_contract": (
            "Return (T, observed) when the event occurs and "
            "(input_length, censored) otherwise."
        ),
        "declared_termination_guarantee": (
            "Return after consuming at most the finite serialized input."
        ),
    }
    assert estimator_anchor["content"][0]["source_estimator"][
        "model_authored_execution_notes"
    ] == {"bounded_outcome": "The censored flag is part of the estimand."}
    assert backend.requests[0].model == TEST_HAIKU_MODEL
    assert backend.requests[0].metadata["model_tier"] == "haiku"
    assert backend.requests[0].max_tokens == 7000
    assert "review_output_token_cap" not in backend.requests[0].metadata
    request_content = backend.requests[0].messages[0]["content"]
    assert "Separate mathematical coherence, proof completeness" in request_content
    assert "symbolic reduction" in request_content
    assert "identity and type of every object" in request_content
    assert "each tool call encodes the proposition" in request_content
    assert "all active candidate text" in request_content
    submit_schema = _submit_schema(backend.requests[0])
    assert "downstream proof obligations separate" in (
        prompt_payload["verdict_policy"]
    )
    assert submit_schema["properties"]["overall_verdict"]["enum"] == [
        "ACCEPT",
        "REVISE",
    ]
    for retired_field in (
        "claim_statuses",
        "dimension_statuses",
        "estimator_execution_checks",
    ):
        assert retired_field not in submit_schema["properties"]
    assert "repair_instructions" not in submit_schema["properties"]
    assert "ordered_components" not in prompt_payload["review_scope"]
    assert "runtime_authored_claim_checklist" not in prompt_payload["review_scope"]
    assert prompt_payload["review_scope"]["execution_handoff_required"] is True
    assert "component_reviews" not in submit_schema["properties"]
    assert "prior_finding_statuses" not in submit_schema["properties"]
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_theory_only_preflight_accepts_without_an_estimator_handoff() -> None:
    theory_material = _with_test_review_workspace(
        _theory_material_without_estimators()
    )
    evidence_contract = build_architect_upstream_research_contract(
        _theory_only_evidence_contract()
    )
    theory_only_payload = _payload(accept=True)
    for review in theory_only_payload["dimension_reviews"]:
        review["evidence_refs"] = [
            "theory.problem_card",
            "theory.derivation_steps",
        ]
    theory_only_payload["estimator_execution_checks"] = []
    theory_only_payload["execution_handoff_status"] = (
        PREFLIGHT_EXECUTION_HANDOFF_NOT_REQUIRED
    )
    backend = _PreflightToolBackend(
        accept=True,
        payload=theory_only_payload,
    )

    packet = _tool_review(
        backend,
        theory_protocol_material=theory_material,
        upstream_research_contract=evidence_contract,
    )
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=theory_material,
        upstream_research_contract=evidence_contract,
    )

    assert material["execution_handoff_required"] is False
    assert material["execution_handoff_available"] is False
    assert "required_review_components" not in material
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["review_scope"]["execution_handoff_required"] is False
    assert packet["review_scope"]["execution_handoff_available"] is False
    assert "runtime_authored_claim_checklist" not in packet["review_scope"]
    prompt_payload = _preflight_prompt_payload(backend.requests[0])
    assert "only when review_scope requests" in prompt_payload["task"]
    assert "otherwise do not invent one" in prompt_payload["verdict_policy"]
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_revise_verdict_can_preserve_findings_and_release_exploratory_handoff() -> None:
    payload = _payload(accept=False)
    payload["execution_handoff_status"] = PREFLIGHT_EXECUTION_HANDOFF_READY
    backend = _PreflightToolBackend(
        accept=False,
        payload=payload,
    )

    packet = _tool_review(backend)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )

    assert packet["overall_verdict"] == "REVISE"
    assert packet["execution_handoff_status"] == (
        PREFLIGHT_EXECUTION_HANDOFF_READY
    )
    assert packet["active_unresolved_finding_ids"]
    schema = _architect_theory_execution_preflight_submit_schema(material)
    handoff_description = schema["properties"]["execution_handoff_status"][
        "description"
    ]
    assert "proof or asymptotic findings remain" in handoff_description
    assert "BLOCKED is reserved" in handoff_description
    assert "internally contradictory" in handoff_description
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_task_contract_does_not_expand_a_runtime_review_checklist() -> None:
    theory_material = _theory_material()
    semantic = theory_material["theory_semantic_material"]
    semantic["theory_derivation_packet"]["claim_index"] = [
        {"id": "stable_claim", "kind": "theorem", "status": "SUPPORTED"},
        {"id": "open_claim", "kind": "conjecture", "status": "OPEN"},
        {"id": "retired_claim", "kind": "lemma", "status": "REJECTED"},
    ]
    theory_material["source_theory_packet_hash"] = stable_hash(semantic)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=theory_material,
        upstream_research_contract={
            "dimension_requirements": {
                "scientific_code": "required",
                "empirical": "required",
                "formal": "required",
            },
            "simulation_targets": ["evaluate the task-requested quantity"],
            "formal_targets": ["formalize the stable claim"],
        },
    )
    schema = _architect_theory_execution_preflight_submit_schema(material)
    prompt_text = build_architect_theory_execution_preflight_prompt(material)
    prompt = json.loads(prompt_text.split("\n\n", 1)[1])

    assert material["execution_handoff_required"] is True
    assert material["execution_handoff_available"] is True
    assert material["formal_sources_applicable"] is True
    assert "required_review_components" not in material
    assert "component_reviews" not in schema["properties"]
    assert "ordered_components" not in prompt["review_scope"]
    assert "runtime_authored_claim_checklist" not in prompt["review_scope"]
    assert all(
        claim_id not in json.dumps(schema, sort_keys=True)
        for claim_id in ("stable_claim", "open_claim", "retired_claim")
    )


def test_executable_preflight_still_rejects_accept_without_an_estimator() -> None:
    theory_material = _with_test_review_workspace(
        _theory_material_without_estimators()
    )
    runtime_contract = {
        "dimension_requirements": {
            **_theory_only_evidence_contract()["dimension_requirements"],
            "scientific_code": "required",
        }
    }
    evidence_contract = build_architect_upstream_research_contract(runtime_contract)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=theory_material,
        upstream_research_contract=evidence_contract,
    )

    assert material["execution_handoff_required"] is True
    assert material["execution_handoff_available"] is False
    with pytest.raises(PacketValidationError) as caught:
        _tool_review(
            _PreflightToolBackend(accept=True),
            theory_protocol_material=theory_material,
            upstream_research_contract=evidence_contract,
        )
    assert "cannot accept without an estimator" in json.dumps(
        caught.value.history,
        sort_keys=True,
    )


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


def test_preflight_reviewer_reads_late_hash_bound_theory_document(
    tmp_path: Path,
) -> None:
    marker = "late_document_claim_marker: E[T_n] / n converges to theta."
    lines = ["# Long theory workspace", ""]
    lines.extend(
        f"Background derivation line {index}: retain the declared assumptions."
        for index in range(1400)
    )
    lines.extend(["", "## Central claim", marker, "Use dominated convergence here."])
    content = "\n".join(lines) + "\n"
    relative_path = "derivations/central_claim.md"
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")

    theory_material = _theory_material()
    semantic = theory_material["theory_semantic_material"]
    semantic["theory_workspace_manifest"] = theory_workspace_document_manifest(
        {relative_path: content},
        workspace_dir=tmp_path,
    )
    semantic["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
    semantic["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    semantic["theory_derivation_packet"]["derivation_steps"] = [
        {
            "id": "legacy_structured_duplicate",
            "claim": "This row indexes mathematics owned by the document.",
            "equation_or_argument": marker,
        }
    ]
    theory_material["source_theory_packet_hash"] = stable_hash(semantic)

    class DocumentInspectionBackend(_PreflightToolBackend):
        def __init__(self) -> None:
            super().__init__(accept=True, cite_sources=False)
            self.marker_line = 0

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "search-authoritative-document",
                        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
                        {"query": "late_document_claim_marker"},
                    )
                )
            if turn == 2:
                search_result = json.loads(
                    request.messages[-1]["content"][0]["content"]
                )
                self.marker_line = search_result["hits"][0]["line_number"]
                return _tool_response(
                    ClientToolCall(
                        "read-authoritative-document",
                        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                        {
                            "path": relative_path,
                            "line_start": self.marker_line,
                            "line_end": self.marker_line + 1,
                        },
                    )
                )
            return _tool_response(
                ClientToolCall(
                    "submit-after-document-read",
                    "submit_theory_preflight_review",
                    self._submission(source_ref=""),
                )
            )

    backend = DocumentInspectionBackend()
    packet = _tool_review(
        backend,
        theory_protocol_material=theory_material,
    )

    initial_prompt = str(backend.requests[0].messages[0]["content"])
    assert marker not in initial_prompt
    prompt_payload = json.loads(
        initial_prompt.split("\n\nThis is a hash-bound catalog", 1)[0]
    )
    document_catalog = prompt_payload["source_material"][
        "authoritative_theory_documents"
    ]
    assert document_catalog == [
        {
            "anchor_id": f"theory.document:{relative_path}",
            "path": relative_path,
            "sha256": document_catalog[0]["sha256"],
            "line_count": len(content.splitlines()),
            "byte_size": len(content.encode("utf-8")),
        }
    ]
    assert all(
        row["artifact_role"] != "authoritative_theory_document"
        for row in prompt_payload["source_material"]["current_theory_anchors"]
    )
    derivation_anchor = next(
        row
        for row in prompt_payload["source_material"]["current_theory_anchors"]
        if row["anchor_id"] == "theory.derivation_steps"
    )
    assert "content" not in derivation_anchor
    assert derivation_anchor["content_access"] == (
        "authoritative_document_tools_or_model_directed_compact_search"
    )
    search_observation = _last_tool_result(backend.requests[1])
    assert search_observation["hits"][0]["line"] == marker
    assert packet["theory_document_inspection_required"] is True
    assert packet["theory_document_inspection_count"] == 2
    assert [
        row["tool"] for row in packet["theory_document_inspection_refs"]
    ] == [
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    ]
    assert marker not in json.dumps(packet)
    assert all(
        "client_tool_session_ref" in call["result_excerpt"]
        for turn in packet["client_tool_loop_history"]
        for call in turn["tool_calls"]
        if not call["is_error"]
        if call["name"]
        in {
            THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
            THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        }
    )


def test_preflight_allows_model_directed_authoritative_document_reads(
    tmp_path: Path,
) -> None:
    relative_path = "derivations/claim_chain.md"
    content = """# Claim chain

## Definition
Define the primitive object directly.

## Main theorem
Derive the conclusion from the primitive definition.

## Rejected route
This abandoned route is explicitly rejected.
"""
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")

    theory_material = _theory_material()
    semantic = theory_material["theory_semantic_material"]
    semantic["theory_workspace_manifest"] = theory_workspace_document_manifest(
        {relative_path: content},
        workspace_dir=tmp_path,
    )
    semantic["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
    semantic["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    semantic["theory_derivation_packet"]["claim_index"] = [
        {
            "id": "definition_primitive",
            "kind": "definition",
            "document_path": relative_path,
            "anchor": "## Definition",
            "depends_on": [],
            "status": "SUPPORTED",
        },
        {
            "id": "theorem_main",
            "kind": "theorem",
            "document_path": relative_path,
            "anchor": "## Main theorem",
            "depends_on": ["definition_primitive"],
            "status": "SUPPORTED",
        },
        {
            "id": "rejected_route",
            "kind": "equation",
            "document_path": relative_path,
            "anchor": "## Rejected route",
            "depends_on": [],
            "status": "REJECTED",
        },
    ]
    theory_material["source_theory_packet_hash"] = stable_hash(semantic)

    class ClaimCoverageBackend(_PreflightToolBackend):
        def __init__(self) -> None:
            payload = _payload(accept=True)
            payload["claim_reviews"] = [
                {
                    "status": "PASS",
                    "independent_check": (
                        "Reconstructed the indexed claim directly from its declared "
                        "definition and dependency."
                    ),
                    "rationale": "The inspected claim transition is coherent.",
                    "evidence_refs": [
                        f"theory.document:{relative_path}",
                    ],
                }
                for _claim_id in ("definition_primitive", "theorem_main")
            ]
            super().__init__(
                accept=True,
                cite_sources=False,
                payload=payload,
            )

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-independent-reconstruction",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {
                            "content": (
                                "# Independent reconstruction\n\nThe primitive should "
                                "determine the theorem through its declared dependency.\n"
                            )
                        },
                    )
                )
            if turn == 2:
                return _tool_response(
                    ClientToolCall(
                        "read-definition",
                        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                        {
                            "path": relative_path,
                            "line_start": 1,
                            "line_end": 4,
                        },
                    )
                )
            if turn == 3:
                return _tool_response(
                    ClientToolCall(
                        "submit-after-model-directed-inspection",
                        "submit_theory_preflight_review",
                        self._submission(source_ref=""),
                    )
                )
            raise AssertionError("review should terminate after its focused inspection")

    backend = ClaimCoverageBackend()
    packet = _tool_review(
        backend,
        theory_protocol_material=theory_material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["theory_document_inspection_count"] == 1
    assert packet["theory_document_inspection_refs"][0]["line_end"] == 4
    assert "component_reviews" not in packet
    assert "runtime_authored_claim_checklist" not in packet["review_scope"]
    submit_properties = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == "submit_theory_preflight_review"
    ).input_schema["properties"]
    assert "claim_statuses" not in submit_properties
    assert "overall_verdict" in submit_properties


def test_one_failed_claim_review_blocks_preflight_acceptance(tmp_path: Path) -> None:
    relative_path = "derivations/two_claims.md"
    content = """# Two claims

## Definition
Define the primitive object.

## Main theorem
Assert an unsupported transition.
"""
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")
    theory_material = _theory_material()
    semantic = theory_material["theory_semantic_material"]
    semantic["theory_workspace_manifest"] = theory_workspace_document_manifest(
        {relative_path: content}, workspace_dir=tmp_path
    )
    semantic["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
    semantic["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    semantic["theory_derivation_packet"]["claim_index"] = [
        {
            "id": "definition_primitive",
            "kind": "definition",
            "document_path": relative_path,
            "anchor": "## Definition",
            "depends_on": [],
            "status": "SUPPORTED",
        },
        {
            "id": "theorem_main",
            "kind": "theorem",
            "document_path": relative_path,
            "anchor": "## Main theorem",
            "depends_on": ["definition_primitive"],
            "status": "SUPPORTED",
        },
    ]
    theory_material["source_theory_packet_hash"] = stable_hash(semantic)
    payload = _payload(accept=True)
    payload["claim_reviews"] = [
        {
            "status": "PASS",
            "independent_check": "Expanded the primitive definition directly.",
            "rationale": "The definition is internally coherent.",
            "evidence_refs": [f"theory.document:{relative_path}"],
        },
        {
            "status": "FAIL",
            "independent_check": (
                "Following the declared dependency yields no implication supporting "
                "the theorem transition."
            ),
            "rationale": "The active theorem has an unsupported step.",
            "evidence_refs": [f"theory.document:{relative_path}"],
        },
    ]
    payload["findings"] = [
        {
            "severity": "critical",
            "category": "invalid_active_claim_transition",
            "summary": "An active theorem transition is unsupported.",
            "observed_behavior": "The conclusion does not follow from its dependency.",
            "expected_behavior": "Every active theorem has a valid derivation or gap.",
            "evidence_refs": [f"theory.document:{relative_path}"],
        }
    ]

    class ClaimFailureBackend(_PreflightToolBackend):
        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-independent-reconstruction",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {
                            "content": (
                                "# Independent reconstruction\n\nThe theorem must follow "
                                "from the primitive definition; no such implication is "
                                "yet available from the question alone.\n"
                            )
                        },
                    )
                )
            if len(self.requests) == 2:
                return _tool_response(
                    ClientToolCall(
                        "read-all-claims",
                        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                        {
                            "path": relative_path,
                            "line_start": 1,
                            "line_end": len(content.splitlines()),
                        },
                    )
                )
            return _tool_response(
                ClientToolCall(
                    "submit-failed-claim",
                    "submit_theory_preflight_review",
                    self._submission(source_ref=""),
                )
            )

    packet = _tool_review(
        ClaimFailureBackend(
            accept=False,
            payload=payload,
            cite_sources=False,
        ),
        theory_protocol_material=theory_material,
    )

    assert packet["overall_verdict"] == "REVISE"
    assert "component_reviews" not in packet
    assert packet["findings"][0]["category"] == (
        "invalid_active_claim_transition"
    )


def test_preflight_requires_report_write_before_compact_submission() -> None:
    class CompactEnvelopeBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.rejection = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                submission = _payload(accept=False)
            else:
                self.rejection = _last_tool_result(request)
                submission = _compact_submission(_payload(accept=False))
            return _tool_response(
                ClientToolCall(
                    f"submit-{len(self.requests)}",
                    "submit_theory_preflight_review",
                    submission,
                )
            )

    backend = CompactEnvelopeBackend()
    packet = _tool_review(backend)

    assert len(backend.requests) == 2
    assert backend.rejection["error"] == "client_tool_input_rejected"
    assert "requires a model-owned Markdown report" in backend.rejection["detail"]
    assert packet["overall_verdict"] == "REVISE"
    rejected = packet["client_tool_loop_history"][0]["tool_calls"][0]
    assert rejected["is_error"] is True


def test_preflight_prior_finding_schema_uses_compact_ordered_array() -> None:
    base_material = {
        "anchor_catalog": [
            {"anchor_id": "theory.estimator_specs"},
            {"anchor_id": "theory.theorem_cards"},
        ],
    }
    one_schema = _architect_theory_execution_preflight_submit_schema(
        {**base_material, "active_prior_finding_ids": ["finding:0"]}
    )
    six_schema = _architect_theory_execution_preflight_submit_schema(
        {
            **base_material,
            "active_prior_finding_ids": [
                f"finding:{index}" for index in range(6)
            ],
        }
    )

    prior_schema = six_schema["properties"]["prior_finding_statuses"]
    assert prior_schema["type"] == "array"
    assert prior_schema["minItems"] == 6
    assert prior_schema["maxItems"] == 6
    assert set(prior_schema["items"]["enum"]) == {
        "UNRESOLVED",
        "RESOLVED_BY_CURRENT_THEORY",
        "RETRACTED_BY_CURRENT_EVIDENCE",
    }
    assert len(json.dumps(six_schema, separators=(",", ":"))) - len(
        json.dumps(one_schema, separators=(",", ":"))
    ) < 400


def test_preflight_client_submit_schema_stays_compact_with_sixteen_claims() -> None:
    large_theory_material = _theory_material()
    large_semantic = large_theory_material["theory_semantic_material"]
    large_semantic["theory_derivation_packet"]["claim_index"] = [
        {
            "id": f"claim_{index}",
            "kind": "lemma",
            "status": "SUPPORTED",
        }
        for index in range(16)
    ]
    large_theory_material["source_theory_packet_hash"] = stable_hash(
        large_semantic
    )
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=large_theory_material,
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    material["active_prior_finding_ids"] = [
        "finding:0",
        "finding:1",
        "finding:2",
    ]
    schema = _architect_theory_execution_preflight_submit_schema(material)
    small_material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    small_material["active_prior_finding_ids"] = list(
        material["active_prior_finding_ids"]
    )
    small_schema = _architect_theory_execution_preflight_submit_schema(small_material)
    assert schema == small_schema
    assert "component_reviews" not in schema["properties"]

    for retired_field in (
        "claim_statuses",
        "dimension_statuses",
        "estimator_execution_checks",
    ):
        assert retired_field not in schema["properties"]
    assert schema["properties"]["overall_verdict"]["enum"] == [
        "ACCEPT",
        "REVISE",
    ]
    prior_schema = schema["properties"]["prior_finding_statuses"]
    assert prior_schema["type"] == "array"
    assert prior_schema["minItems"] == 3
    assert prior_schema["maxItems"] == 3
    assert "review_report_sha256" in schema["required"]
    assert "review_report_markdown" not in schema["properties"]
    assert "report_evidence_refs" in schema["required"]
    assert schema["properties"]["report_evidence_refs"]["maxItems"] == 32
    assert "enum" not in schema["properties"]["report_evidence_refs"]["items"]
    assert "maxItems" not in schema["properties"]["findings"]
    compact_size = len(json.dumps(schema, separators=(",", ":")))
    assert compact_size < 5_000


def test_client_tool_preflight_persists_markdown_referee_report(
    tmp_path: Path,
) -> None:
    relative_path = "derivations/candidate.md"
    theory_text = (
        "# Candidate\n\n"
        "Define the finite procedure and derive its claimed identity.\n"
    )
    workspace_dir = tmp_path / "run" / "theory_workspaces" / "workspace"
    theory_path = workspace_dir / relative_path
    theory_path.parent.mkdir(parents=True)
    theory_path.write_text(theory_text, encoding="utf-8")
    theory_material = _theory_material()
    semantic = theory_material["theory_semantic_material"]
    semantic["theory_workspace_manifest"] = theory_workspace_document_manifest(
        {relative_path: theory_text},
        workspace_dir=workspace_dir,
    )
    semantic["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
    semantic["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    semantic["theory_derivation_packet"]["claim_index"] = [
        {
            "id": "finite_identity",
            "kind": "equation",
            "document_path": relative_path,
            "depends_on": [],
            "status": "SUPPORTED",
        }
    ]
    theory_material["source_theory_packet_hash"] = stable_hash(semantic)
    report = (
        "# Independent theory preflight\n\n"
        "I reconstructed the finite identity from the declared definition and "
        "checked the no-event boundary. The typed censored outcome keeps the "
        "procedure total, and no generated execution result is assumed.\n"
    )

    class CompactReportBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return _tool_response(
                    ClientToolCall(
                        "read-candidate",
                        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                        {
                            "path": relative_path,
                            "line_start": 1,
                            "line_end": len(theory_text.splitlines()),
                        },
                    )
                )
            if len(self.requests) == 2:
                return _tool_response(
                    ClientToolCall(
                        "write-report",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {"content": report},
                    )
                )
            return _tool_response(
                ClientToolCall(
                    "submit-compact-report",
                    "submit_theory_preflight_review",
                    {
                        "review_report_sha256": hashlib.sha256(
                            report.encode("utf-8")
                        ).hexdigest(),
                        "report_evidence_refs": [
                            f"theory.document:{relative_path}",
                            "theory.estimator_specs",
                        ],
                        "overall_verdict": "ACCEPT",
                        "execution_handoff_status": (
                            PREFLIGHT_EXECUTION_HANDOFF_READY
                        ),
                        "findings": [],
                    },
                )
            )

    backend = CompactReportBackend()
    packet = _tool_review(
        backend,
        theory_protocol_material=theory_material,
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["review_transport"] == (
        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_REVIEW_TRANSPORT
    )
    assert "review_report_markdown" not in packet
    review_document = packet["review_report"]
    assert review_document["persisted"] is True
    review_path = Path(review_document["path"])
    assert review_path.read_text(encoding="utf-8") == report
    assert review_path.is_relative_to(tmp_path / "run" / "theory_reviews")
    assert "theory_independent_reconstruction_chronology" not in packet
    assert len(backend.requests) == 3
    assert "component_reviews" not in packet
    assert "runtime_authored_claim_checklist" not in packet["review_scope"]
    assert review_document["sha256"] == hashlib.sha256(
        report.encode("utf-8")
    ).hexdigest()
    assert review_document["evidence_refs"] == [
        f"theory.document:{relative_path}",
        "theory.estimator_specs",
    ]
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=theory_material,
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    escaped_packet = deepcopy(packet)
    escaped_packet["review_report"]["path"] = str(
        tmp_path / "outside-review-workspace.md"
    )
    assert any(
        "path escapes its workspace" in error
        for error in validate_architect_theory_execution_preflight_packet(
            escaped_packet,
            material=material,
        )
    )
    review_path.write_text(report + "tampered\n", encoding="utf-8")
    assert "theory execution preflight review report hash mismatch" in (
        validate_architect_theory_execution_preflight_packet(
            packet,
            material=material,
        )
    )
    submit_schema = backend.requests[0].tools[-1].input_schema
    assert "claim_reviews" not in submit_schema["properties"]
    assert "dimension_reviews" not in submit_schema["properties"]
    assert "claim_statuses" not in submit_schema["properties"]


def test_preflight_referee_owns_hash_bound_report_iteration() -> None:
    report_v1 = (
        "# Independent referee report\n\n"
        "The declared finite mapping is total, but the boundary argument is pending.\n"
    )
    report_v2 = report_v1.replace(
        "the boundary argument is pending",
        "I checked the boundary argument directly from the declared definition",
    )
    report_v1_sha = hashlib.sha256(report_v1.encode("utf-8")).hexdigest()
    report_v2_sha = hashlib.sha256(report_v2.encode("utf-8")).hexdigest()

    class ReportWorkspaceBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.read_observation = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-report-v1",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {"content": report_v1},
                    )
                )
            observation = _last_tool_result(request)
            if turn == 2:
                assert observation["sha256"] == report_v1_sha
                return _tool_response(
                    ClientToolCall(
                        "read-report-v1",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_READ_REPORT_TOOL,
                        {
                            "expected_sha256": report_v1_sha,
                            "line_start": 1,
                            "line_end": len(report_v1.splitlines()),
                        },
                    )
                )
            if turn == 3:
                self.read_observation = observation
                return _tool_response(
                    ClientToolCall(
                        "edit-report-v2",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
                        {
                            "expected_sha256": report_v1_sha,
                            "old_text": "the boundary argument is pending",
                            "new_text": (
                                "I checked the boundary argument directly from the "
                                "declared definition"
                            ),
                        },
                    )
                )
            assert observation["sha256"] == report_v2_sha
            return _tool_response(
                ClientToolCall(
                    "submit-report-v2",
                    "submit_theory_preflight_review",
                    _hash_bound_submission(
                        _payload(accept=True),
                        report_sha256=report_v2_sha,
                        report_content=report_v2,
                    ),
                )
            )

    backend = ReportWorkspaceBackend()
    packet = _tool_review(backend)

    assert packet["overall_verdict"] == "ACCEPT"
    assert backend.read_observation["content"] == report_v1.rstrip("\n")
    assert Path(packet["review_report"]["path"]).read_text(
        encoding="utf-8"
    ) == report_v2
    assert packet["review_report"]["sha256"] == report_v2_sha
    assert packet["client_tool_loop_turns"] == 4
    assert packet["client_tool_loop_tool_calls"] == 4
    assert {request.model for request in backend.requests} == {TEST_HAIKU_MODEL}
    persisted_history = json.dumps(packet["client_tool_loop_history"])
    assert report_v1 not in persisted_history
    assert report_v2 not in persisted_history


def test_preflight_returns_stale_report_hash_to_same_referee() -> None:
    initial_report = "# Referee report\n\nA claim remains uncertain.\n"
    revised_report = initial_report.replace("uncertain", "independently checked")
    initial_sha = hashlib.sha256(initial_report.encode("utf-8")).hexdigest()
    revised_sha = hashlib.sha256(revised_report.encode("utf-8")).hexdigest()

    class StaleHashBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.rejection = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-initial-report",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {"content": initial_report},
                    )
                )
            if turn == 2:
                return _tool_response(
                    ClientToolCall(
                        "edit-with-stale-hash",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
                        {
                            "expected_sha256": "0" * 64,
                            "old_text": "uncertain",
                            "new_text": "independently checked",
                        },
                    )
                )
            self.rejection = _last_tool_result(request)
            return _tool_response(
                ClientToolCall(
                    "edit-with-current-hash",
                    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_EDIT_REPORT_TOOL,
                    {
                        "expected_sha256": initial_sha,
                        "old_text": "uncertain",
                        "new_text": "independently checked",
                    },
                ),
                ClientToolCall(
                    "submit-revised-report",
                    "submit_theory_preflight_review",
                    _hash_bound_submission(
                        _payload(accept=True),
                        report_sha256=revised_sha,
                        report_content=revised_report,
                    ),
                ),
            )

    backend = StaleHashBackend()
    packet = _tool_review(backend)

    assert backend.rejection["error"] == "client_tool_input_rejected"
    assert "expected_sha256 is stale" in backend.rejection["detail"]
    assert Path(packet["review_report"]["path"]).read_text(
        encoding="utf-8"
    ) == revised_report
    assert packet["client_tool_loop_turns"] == 3
    assert packet["client_tool_loop_tool_calls"] == 4


def test_preflight_returns_obsolete_terminal_field_to_same_referee() -> None:
    report = (
        "# Independent referee report\n\n"
        "I reconstructed the target and compared the candidate's decisive transition.\n"
    )
    report_sha = hashlib.sha256(report.encode("utf-8")).hexdigest()

    class EnvelopeCorrectionBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.rejection = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-report",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {"content": report},
                    )
                )
            submission = _hash_bound_submission(
                _payload(accept=True),
                report_sha256=report_sha,
                report_content=report,
            )
            if len(self.requests) == 2:
                submission["component_reviews"] = [
                    {"status": "PASS", "report_line_start": 1, "report_line_end": 99}
                ]
                return _tool_response(
                    ClientToolCall(
                        "submit-obsolete-checklist",
                        "submit_theory_preflight_review",
                        submission,
                    )
                )
            self.rejection = _last_tool_result(request)
            return _tool_response(
                ClientToolCall(
                    "submit-compact-envelope",
                    "submit_theory_preflight_review",
                    submission,
                )
            )

    backend = EnvelopeCorrectionBackend()
    packet = _tool_review(backend)

    assert backend.rejection["error"] == "client_tool_input_rejected"
    assert "component_reviews" in backend.rejection["detail"]
    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["client_tool_loop_turns"] == 3


def test_preflight_rejects_tampered_report_draft_before_model_call() -> None:
    report = "# Referee report\n\nThis is an incomplete independent audit.\n"
    theory_material = _with_test_review_workspace(_theory_material())

    class WriteThenStopBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return _tool_response(
                    ClientToolCall(
                        "write-report-before-checkpoint",
                        ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL,
                        {"content": report},
                    )
                )
            return _tool_response()

    with pytest.raises(PacketValidationError) as first_error:
        _tool_review(
            WriteThenStopBackend(),
            theory_protocol_material=theory_material,
        )
    checkpoint = first_error.value.recovery_checkpoint
    draft_path = Path(checkpoint["review_report_draft"]["path"])
    draft_path.write_text(report + "tampered\n", encoding="utf-8")

    class MustNotRun:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            raise AssertionError("tampered draft must fail before the model call")

    blocked_backend = MustNotRun()
    with pytest.raises(PacketValidationError, match="draft is stale"):
        _tool_review(
            blocked_backend,
            theory_protocol_material=theory_material,
            recovery_checkpoint=checkpoint,
        )
    assert blocked_backend.requests == []


def test_preflight_estimator_transport_is_compact_and_semantically_owned() -> None:
    schema = _architect_theory_execution_preflight_submit_schema(
        {
            "anchor_catalog": [{"anchor_id": "theory.estimator_specs"}],
            "active_prior_finding_ids": [],
        }
    )
    assert "estimator_execution_checks" not in schema["properties"]
    assert schema["properties"]["overall_verdict"]["enum"] == [
        "ACCEPT",
        "REVISE",
    ]
    assert "review_report_sha256" in schema["required"]
    assert "review_report_markdown" not in schema["properties"]
    assert "report_evidence_refs" in schema["required"]
    assert "enum" not in schema["properties"]["report_evidence_refs"]["items"]
    assert "component_reviews" not in schema["properties"]


def test_preflight_cannot_accept_a_failed_independent_identity_check() -> None:
    packet, _backend = _review(accept=False)
    packet["overall_verdict"] = "ACCEPT"

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

    assert any("overall verdict contradicts" in error for error in errors)


def test_preflight_cannot_accept_pass_with_a_model_reported_blocking_gap() -> None:
    packet, _backend = _review(accept=False)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    packet["overall_verdict"] = "ACCEPT"

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )

    assert any("overall verdict contradicts" in error for error in errors)


def test_preflight_revise_requires_a_model_authored_blocking_finding() -> None:
    packet, _backend = _review(accept=True)
    material = build_architect_theory_execution_preflight_material(
        question=_question(),
        theory_protocol_material=_theory_material(),
        upstream_research_contract={
            "formal_targets": [],
            "simulation_targets": ["evaluate the declared risk"],
        },
    )
    packet["overall_verdict"] = "REVISE"

    errors = validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    )

    assert any("needs at least one finding" in error for error in errors)
    assert any("overall verdict contradicts" in error for error in errors)


def test_preflight_carries_model_owned_finding_without_checklist_rows() -> None:
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
    assert "runtime_authored_claim_checklist" not in packet["review_scope"]
    assert "dimension_reviews" not in packet
    assert "estimator_execution_checks" not in packet
    assert "derived_consistency_warnings" not in packet
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_returns_inconsistent_disposition_to_same_model() -> None:
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
            self.rejection = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            candidate = _compact_submission(deepcopy(payload))
            candidate["overall_verdict"] = (
                "ACCEPT" if len(self.requests) == 1 else "REVISE"
            )
            if len(self.requests) > 1:
                self.rejection = _last_tool_result(request)
            return _tool_response(
                ClientToolCall(
                    f"submit-{len(self.requests)}",
                    "submit_theory_preflight_review",
                    candidate,
                )
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
    assert packet["overall_verdict"] == "REVISE"
    assert packet["findings"][0]["category"] == (
        "unestablished_theorem_hypothesis"
    )
    assert "runtime_estimator_status_normalizations" not in packet
    assert backend.rejection["error"] == "preflight_submission_rejected"
    assert any(
        "overall verdict contradicts" in error
        for error in backend.rejection["validation_errors"]
    )
    assert validate_architect_theory_execution_preflight_packet(
        packet,
        material=material,
    ) == []


def test_preflight_regenerates_all_pass_finding_conflict_with_same_model() -> None:
    class AllPassFindingBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.rejection = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = _payload(accept=True)
                payload["findings"] = deepcopy(_payload(accept=False)["findings"])
                submission = _compact_submission(payload)
                submission["overall_verdict"] = "ACCEPT"
            else:
                self.rejection = _last_tool_result(request)
                submission = _compact_submission(_payload(accept=True))
            return _tool_response(
                ClientToolCall(
                    f"submit-{len(self.requests)}",
                    "submit_theory_preflight_review",
                    submission,
                )
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
    )

    assert packet["overall_verdict"] == "ACCEPT"
    assert packet["findings"] == []
    assert len(backend.requests) == 2
    assert {request.model for request in backend.requests} == {TEST_HAIKU_MODEL}
    assert any(
        "overall verdict contradicts" in error
        for error in backend.rejection["validation_errors"]
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
        prior_finding_ledger=prior_ledger,
    )

    submit_schema = _submit_schema(backend.requests[0])
    prior_review_schema = submit_schema["properties"]["prior_finding_statuses"]
    assert prior_review_schema["type"] == "array"
    assert prior_review_schema["minItems"] == 1
    assert prior_review_schema["maxItems"] == 1
    assert "RESOLVED_BY_CURRENT_THEORY" in prior_review_schema["items"]["enum"]
    prompt_payload = _preflight_prompt_payload(backend.requests[0])
    prior_slot = prompt_payload["review_scope"][
        "active_prior_finding_slots"
    ][0]
    assert prior_slot["finding_id"] == prior_finding_ids[0]
    assert prior_slot["prior_obligation"]["summary"] == (
        prior_ledger[0]["finding"]["summary"]
    )
    assert "observed_behavior" not in prior_slot["prior_obligation"]
    assert prior_ledger[0]["finding"]["observed_behavior"] not in (
        str(backend.requests[0].messages[0]["content"])
    )
    assert prior_slot["prior_obligation"]["expected_behavior"] == (
        prior_ledger[0]["finding"]["expected_behavior"]
    )
    assert prior_slot["review_basis"] == "current_theory_anchors_only"
    finding_definition = submit_schema["$defs"]["finding"]
    prior_index_schema = finding_definition["properties"]["prior_finding_index"]
    assert prior_index_schema["minimum"] == -1
    assert prior_index_schema["maximum"] == 0
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
        prior_finding_ledger=prior_ledger,
    )

    prior_status_schema = _submit_schema(backend.requests[0])["properties"][
        "prior_finding_statuses"
    ]["items"]
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
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 1
    submit_schema = _submit_schema(backend.requests[0])
    finding_schema = submit_schema["$defs"]["finding"]
    assert "prior_finding_id" not in finding_schema["properties"]
    assert finding_schema["properties"]["prior_finding_index"]["maximum"] == 0
    assert "finding_id" not in finding_schema["properties"]
    prior_schema = submit_schema["properties"]["prior_finding_statuses"]["items"]
    assert "UNRESOLVED" in prior_schema["enum"]
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
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 1
    assert "current_finding" not in _submit_schema(backend.requests[0])["$defs"][
        "finding"
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
    assert packet["client_tool_loop_turns"] == 1


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
            self.rejection = {}

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                payload = initial_payload
            else:
                self.rejection = _last_tool_result(request)
                payload = deepcopy(initial_payload)
                payload["prior_finding_reviews"] = deepcopy(resolved_rows)
            return _tool_response(
                ClientToolCall(
                    f"submit-{len(self.requests)}",
                    "submit_theory_preflight_review",
                    _compact_submission(payload),
                )
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
        prior_finding_ledger=prior_ledger,
    )

    assert len(backend.requests) == 2
    assert backend.rejection["error"] == "preflight_submission_rejected"
    assert any(
        "resolve every active prior finding_id exactly once" in error
        for error in backend.rejection["validation_errors"]
    )
    assert [
        row["finding_id"] for row in packet["prior_finding_reviews"]
    ] == prior_finding_ids
    assert packet["overall_verdict"] == "ACCEPT"


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

    theory_only_question = OpenResearchQuestion(
        id="generic_resource_bounded_procedure",
        title="Review an ideal procedure and its finite observation",
        description=(
            "Develop and evaluate a statistical procedure whose ideal definition "
            "may consume a data stream of unspecified length."
        ),
        task_intent={
            "theory": "required",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    )
    result = architect_preexecution_metric_protocol_rejection_result(
        task=AgentTask(
            task_id="architect:generic-preflight-rejection",
            owner_subsystem="ArchitectCoordinator",
            objective="Route the rejected theory handoff before coding.",
        ),
        question=theory_only_question,
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
    assert result.next_task.budget[RUNTIME_CONTINUATION_BUDGET_MARKER_KEY] == {
        "scope": "workspace_continuation",
        "parent_task_id": "architect:generic-preflight-rejection",
        "next_task_id": result.next_task.task_id,
        "parent_owner_subsystem": "ArchitectCoordinator",
        "owner_subsystem": "TheoryDeveloper",
    }
    assert result.next_task.inputs["question"]["task_intent"] == (
        theory_only_question.task_intent
    )
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
    assert result.next_task.inputs["environment_feedback"][
        "continuation_budget_authority"
    ] == "AgentRuntime.max_iterations"
    assert "architect_route_required" not in result.next_task.inputs[
        "environment_feedback"
    ]
    assert "source_workspace_return_required" not in result.next_task.inputs[
        "environment_feedback"
    ]
    assert "runtime_selected_owner" not in result.next_task.inputs[
        "environment_feedback"
    ]


def test_metric_author_prompt_requires_quantified_finite_run_uncertainty() -> None:
    accepted_packet, _backend = _review(accept=True)

    class Reviewer:
        config = type("Config", (), {"model_tier": "haiku"})()

        def review_theory_execution_preflight(self, **_kwargs):
            return accepted_packet

    provider = _Backend({})
    with pytest.raises(PacketValidationError) as exc_info:
        author_reviewed_architect_metric_requirements(
            provider=provider,
            config=ArchitectMetricContractAuthoringConfig(
                model_tier="haiku",
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

    assert exc_info.value.validation_label == (
        "LLM Architect metric-requirement packet"
    )
    assert exc_info.value.recovery_checkpoint["artifact_kind"] == (
        "MetricProtocolWorkspaceCheckpoint"
    )
    assert exc_info.value.recovery_checkpoint["runtime_edited_content"] is False
    assert exc_info.value.recovery_checkpoint["automatic_retry_authorized"] is False
    assert provider.requests
    request = provider.requests[0]
    prompt = str(request.messages[0]["content"])
    assert "quantitative uncertainty or sampling-error calculation" in prompt
    assert "'stringent but attainable' are not evidence" in prompt
    assert "actual comparison scale" in prompt
    assert "distinguish absolute error, relative error" in prompt
    assert "bare O(1/sqrt(n)) rate" in prompt
    assert "does not alone justify a tight finite-run threshold" in prompt
    assert "exactly one compact evaluator protocol" in prompt
    assert "Do not expand scenarios or moments into repeated schema rows" in prompt
    assert "top-level acceptance_passed" in prompt
    assert "gate_fields" not in prompt
    assert len(prompt) < 10_000
    assert [tool.name for tool in request.tools] == [
        METRIC_PROTOCOL_WORKSPACE_READ_TOOL,
        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
    ]
    assert request.enable_prompt_caching is True
    assert request.disable_parallel_tool_use is True
    assert request.metadata["full_packet_regeneration_required"] is False
    assert request.metadata["document_body_in_terminal_tool"] is False
    assert request.metadata["runtime_initialized_structural_scaffold"] is True
    assert request.metadata["source_acceptance_mode"] is True
    assert "metric_protocol.md" in request.system_prompt
    assert request.tools[2].input_schema["required"] == [
        "expected_sha256",
        "required_runtime_replicates",
        "evaluator_id",
        "scientific_rationale",
    ]
    assert request.max_tokens == 8000
    assert "required_runtime_replicates" in prompt


def test_metric_protocol_edit_batch_is_hash_bound_and_atomic(
    tmp_path: Path,
) -> None:
    initial_document = '{"a":0,"b":0}\n'
    revised_document = '{"a":1,"b":2}\n'
    initial_sha256 = hashlib.sha256(initial_document.encode("utf-8")).hexdigest()
    revised_sha256 = hashlib.sha256(revised_document.encode("utf-8")).hexdigest()

    def build_validated_packet(
        content: str,
    ) -> tuple[dict[str, object] | None, list[str]]:
        value = json.loads(content)
        return {"packet_id": "metric-authoring:atomic", **value}, []

    class RecoveringAtomicEditBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                edits = [
                    {"old_text": '"a":0', "new_text": '"a":1'},
                    {"old_text": '"missing":0', "new_text": '"missing":1'},
                ]
            elif len(self.requests) == 2:
                edits = [
                    {"old_text": '"a":0', "new_text": '"a":1'},
                    {"old_text": '"b":0', "new_text": '"b":2'},
                ]
            else:
                return _tool_response(
                    ClientToolCall(
                        "hash-only-commit",
                        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
                        {"expected_sha256": revised_sha256},
                    )
                )
            return _tool_response(
                ClientToolCall(
                    f"exact-edit-{len(self.requests)}",
                    METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                    {
                        "expected_parent_sha256": initial_sha256,
                        "edits": edits,
                    },
                )
            )

    backend = RecoveringAtomicEditBackend()
    result = _run_metric_protocol_workspace(
        provider=backend,  # type: ignore[arg-type]
        config=ArchitectMetricContractAuthoringConfig(
            model_tier="haiku",
        ),
        request_model=TEST_HAIKU_MODEL,
        user_message="Apply an atomic revision and commit.",
        build_validated_packet=build_validated_packet,
        prior_document_content=initial_document,
        workspace_dir=tmp_path,
        session_id="metric-protocol-atomic-failure",
    )

    first_edit = result.loop.history[0]["tool_calls"][0]
    assert first_edit["is_error"] is True
    assert "observed 0 matches at edit index 1" in first_edit["result_excerpt"]
    assert result.loop.runtime_executed_tool_calls == 3
    edit_schema = backend.requests[0].tools[1].input_schema
    assert edit_schema["required"] == [
        "expected_parent_sha256",
        "edits",
    ]
    assert result.document_content == revised_document
    assert (tmp_path / "metric_protocol.json").read_text(
        encoding="utf-8"
    ) == revised_document


def test_fresh_metric_protocol_keeps_science_in_markdown_and_commits_metadata(
    tmp_path: Path,
) -> None:
    draft_protocol = (
        "# Confirmatory protocol\n\n"
        "Measure $P(p \\leq 0.1)$ in each frozen scenario.\n"
    )
    protocol = (
        "# Confirmatory protocol\n\n"
        "Measure $P(p \\leq 0.1)$ in each frozen scenario.\n\n"
        "Accept exactly when every upper confidence bound is at most 0.1.\n"
    )
    initial_sha256 = hashlib.sha256(
        METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT.encode("utf-8")
    ).hexdigest()
    draft_sha256 = hashlib.sha256(draft_protocol.encode("utf-8")).hexdigest()
    protocol_sha256 = hashlib.sha256(protocol.encode("utf-8")).hexdigest()
    observed_payloads: list[dict[str, object]] = []

    def build_validated_packet(
        content: str,
    ) -> tuple[dict[str, object] | None, list[str]]:
        value = json.loads(content)
        observed_payloads.append(value)
        if "every upper confidence bound" not in value["acceptance_protocol"]:
            return None, ["decision rule is incomplete"]
        return {
            "packet_id": "metric-authoring:markdown",
            "empirical_metric_requirement_set_id": "metric-set:markdown",
            **value,
        }, []

    class MarkdownProtocolBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                return _tool_response(
                    ClientToolCall(
                        "read-markdown-protocol",
                        METRIC_PROTOCOL_WORKSPACE_READ_TOOL,
                        {},
                    )
                )
            if len(self.requests) == 2:
                return _tool_response(
                    ClientToolCall(
                        "write-markdown-protocol",
                        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                        {
                            "expected_parent_sha256": initial_sha256,
                            "edits": [{
                                "old_text": (
                                    METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT
                                ),
                                "new_text": draft_protocol,
                            }],
                        },
                    )
                )
            if len(self.requests) == 3:
                return _tool_response(
                    ClientToolCall(
                        "commit-incomplete-markdown-protocol",
                        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
                        {
                            "expected_sha256": draft_sha256,
                            "required_runtime_replicates": 2000,
                            "evaluator_id": "finite_sample_calibration",
                            "scientific_rationale": (
                                "The replicate count targets the declared Monte Carlo "
                                "uncertainty before outcomes."
                            ),
                        },
                    )
                )
            if len(self.requests) == 4:
                return _tool_response(
                    ClientToolCall(
                        "complete-markdown-protocol",
                        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                        {
                            "expected_parent_sha256": draft_sha256,
                            "edits": [{
                                "old_text": draft_protocol,
                                "new_text": protocol,
                            }],
                        },
                    )
                )
            if len(self.requests) == 5:
                return _tool_response(
                    ClientToolCall(
                        "commit-markdown-protocol",
                        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
                        {
                            "expected_sha256": protocol_sha256,
                            "required_runtime_replicates": 2000,
                            "evaluator_id": "finite_sample_calibration",
                            "scientific_rationale": (
                                "The replicate count targets the declared Monte Carlo "
                                "uncertainty before outcomes."
                            ),
                        },
                    )
                )
            raise AssertionError("metric protocol workspace exceeded expected turns")

    backend = MarkdownProtocolBackend()
    result = _run_metric_protocol_workspace(
        provider=backend,  # type: ignore[arg-type]
        config=ArchitectMetricContractAuthoringConfig(
            model_tier="haiku",
        ),
        request_model=TEST_HAIKU_MODEL,
        user_message="Author one confirmatory protocol.",
        build_validated_packet=build_validated_packet,
        initial_document_content=METRIC_PROTOCOL_WORKSPACE_SOURCE_INITIAL_DOCUMENT,
        workspace_dir=tmp_path,
        session_id="metric-protocol-markdown",
        source_acceptance_mode=True,
    )

    assert result.document_content == protocol
    assert result.relative_document_path == "metric_protocol.md"
    assert (tmp_path / "metric_protocol.md").read_text(encoding="utf-8") == protocol
    assert not (tmp_path / "metric_protocol.json").exists()
    expected_payload = {
        "required_runtime_replicates": 2000,
        "evaluator_id": "finite_sample_calibration",
        "scientific_rationale": (
            "The replicate count targets the declared Monte Carlo uncertainty "
            "before outcomes."
        ),
    }
    assert observed_payloads == [
        {**expected_payload, "acceptance_protocol": draft_protocol},
        {**expected_payload, "acceptance_protocol": protocol},
    ]
    rejected_commit = result.loop.history[2]["tool_calls"][0]
    assert rejected_commit["is_error"] is True
    assert "decision rule is incomplete" in rejected_commit["result_excerpt"]
    commit_schema = backend.requests[0].tools[2].input_schema
    assert commit_schema["required"] == [
        "expected_sha256",
        "required_runtime_replicates",
        "evaluator_id",
        "scientific_rationale",
    ]
    assert backend.requests[0].metadata["source_acceptance_mode"] is True


def test_metric_protocol_reviewer_feedback_continues_same_editable_workspace(
    tmp_path: Path,
) -> None:
    invalid_document = '{\n  "value": 0\n}\n'
    initial_document = '{\n  "value": 1\n}\n'
    revised_document = '{\n  "value": 2\n}\n'
    invalid_sha256 = hashlib.sha256(invalid_document.encode("utf-8")).hexdigest()
    initial_sha256 = hashlib.sha256(initial_document.encode("utf-8")).hexdigest()
    revised_sha256 = hashlib.sha256(revised_document.encode("utf-8")).hexdigest()
    scaffold_sha256 = hashlib.sha256(
        METRIC_PROTOCOL_WORKSPACE_INITIAL_DOCUMENT.encode("utf-8")
    ).hexdigest()

    def build_validated_packet(
        content: str,
    ) -> tuple[dict[str, object] | None, list[str]]:
        try:
            value = json.loads(content)
        except json.JSONDecodeError as exc:
            return None, [f"invalid JSON: {exc.msg}"]
        if not isinstance(value, dict) or value.get("value") not in {1, 2}:
            return None, ["value must be one of the test candidates"]
        return {
            "packet_id": f"metric-authoring:{value['value']}",
            "empirical_metric_requirement_set_id": f"metric-set:{value['value']}",
            "value": value["value"],
        }, []

    class MetricWorkspaceBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                return _tool_response(
                    ClientToolCall(
                        "edit-invalid-protocol",
                        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                        {
                            "expected_parent_sha256": scaffold_sha256,
                            "edits": [{
                                "old_text": METRIC_PROTOCOL_WORKSPACE_INITIAL_DOCUMENT,
                                "new_text": invalid_document,
                            }],
                        },
                    )
                )
            if turn == 2:
                return _tool_response(
                    ClientToolCall(
                        "commit-invalid-protocol",
                        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
                        {"expected_sha256": invalid_sha256},
                    )
                )
            if turn == 3:
                return _tool_response(
                    ClientToolCall(
                        "edit-initial-protocol",
                        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                        {
                            "expected_parent_sha256": invalid_sha256,
                            "edits": [{
                                "old_text": invalid_document,
                                "new_text": initial_document,
                            }],
                        },
                    )
                )
            if turn == 4:
                return _tool_response(
                    ClientToolCall(
                        "commit-initial-protocol",
                        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
                        {"expected_sha256": initial_sha256},
                    )
                )
            if turn == 5:
                return _tool_response(
                    ClientToolCall(
                        "edit-reviewed-protocol",
                        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                        {
                            "expected_parent_sha256": initial_sha256,
                            "edits": [{
                                "old_text": initial_document,
                                "new_text": revised_document,
                            }],
                        },
                    )
                )
            if turn == 6:
                return _tool_response(
                    ClientToolCall(
                        "commit-reviewed-protocol",
                        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
                        {"expected_sha256": revised_sha256},
                    )
                )
            raise AssertionError("metric protocol workspace exceeded expected turns")

    backend = MetricWorkspaceBackend()
    config = ArchitectMetricContractAuthoringConfig(
        model_tier="haiku",
    )
    assert not hasattr(config, "max_validation_retries")
    first = _run_metric_protocol_workspace(
        provider=backend,  # type: ignore[arg-type]
        config=config,
        request_model=TEST_HAIKU_MODEL,
        user_message="Author the initial protocol from the accepted theory.",
        build_validated_packet=build_validated_packet,
        workspace_dir=tmp_path,
        session_id="metric-protocol-source-owner",
    )
    reviewer_observation = (
        "Independent reviewer finding: the current finite-run threshold is too "
        "strict for its declared uncertainty calculation. Revise the protocol."
    )
    second = _run_metric_protocol_workspace(
        provider=backend,  # type: ignore[arg-type]
        config=config,
        request_model=TEST_HAIKU_MODEL,
        user_message=reviewer_observation,
        build_validated_packet=build_validated_packet,
        prior_messages=first.loop.messages,
        prior_document_content=first.document_content,
        workspace_dir=tmp_path,
        session_id="metric-protocol-source-owner",
        revision_index=1,
    )

    assert len(backend.requests) == 6
    rejected_submission = _last_tool_result(backend.requests[2])
    assert rejected_submission["error"] == "metric_protocol_submission_rejected"
    assert rejected_submission["current_sha256"] == invalid_sha256
    assert rejected_submission["validation_errors"] == [
        "value must be one of the test candidates"
    ]
    assert tuple(backend.requests[4].messages[:-1]) == first.loop.messages
    assert backend.requests[4].messages[-1] == {
        "role": "user",
        "content": reviewer_observation,
    }
    assert backend.requests[0].system_prompt == backend.requests[2].system_prompt
    assert [tool.name for tool in backend.requests[0].tools] == [
        tool.name for tool in backend.requests[2].tools
    ]
    assert [
        call["name"]
        for turn in second.loop.history
        for call in turn["tool_calls"]
    ] == [
        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
    ]
    assert second.document_content == revised_document
    assert (tmp_path / "metric_protocol.json").read_text(
        encoding="utf-8"
    ) == revised_document
    assert second.packet["value"] == 2
    assert second.loop.runtime_executed_tool_calls == 2
    commit_calls = [
        block
        for loop in (first.loop, second.loop)
        for message in loop.messages
        for block in (
            message.get("content", [])
            if isinstance(message.get("content"), list)
            else []
        )
        if block.get("type") == "tool_use"
        and block.get("name") == METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL
    ]
    assert commit_calls
    assert all(set(call["input"]) == {"expected_sha256"} for call in commit_calls)
    assert second.session_ref["session_id"] == "metric-protocol-source-owner"
    assert first.session_ref["relative_path"] != second.session_ref["relative_path"]
    assert second.session_ref["transcript_fingerprint"] == (
        second.loop.transcript_fingerprint
    )


def test_metric_protocol_external_file_survives_truncated_edit_input(
    tmp_path: Path,
) -> None:
    valid_document = '{\n  "value": 1\n}\n'
    scaffold_sha256 = hashlib.sha256(
        METRIC_PROTOCOL_WORKSPACE_INITIAL_DOCUMENT.encode("utf-8")
    ).hexdigest()
    valid_sha256 = hashlib.sha256(valid_document.encode("utf-8")).hexdigest()

    def build_validated_packet(
        content: str,
    ) -> tuple[dict[str, object] | None, list[str]]:
        value = json.loads(content)
        if value != {"value": 1}:
            return None, ["value must equal one"]
        return {
            "packet_id": "metric-authoring:one",
            "empirical_metric_requirement_set_id": "metric-set:one",
        }, []

    class TruncatedEditBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                call = ClientToolCall(
                    "truncated-edit",
                    METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                    {"expected_parent_sha256": scaffold_sha256},
                )
                return ClientToolTurnResponse(
                    content_blocks=(
                        {
                            "type": "tool_use",
                            "id": call.call_id,
                            "name": call.name,
                            "input": dict(call.input),
                        },
                    ),
                    tool_calls=(call,),
                    text="",
                    provider="anthropic",
                    model=TEST_HAIKU_MODEL,
                    metadata={
                        "client_tool_transport": True,
                        "tools_executed_by_backend": False,
                        "provider_stop_reason": "max_tokens",
                    },
                )
            if len(self.requests) == 2:
                return _tool_response(
                    ClientToolCall(
                        "complete-edit",
                        METRIC_PROTOCOL_WORKSPACE_EDIT_TOOL,
                        {
                            "expected_parent_sha256": scaffold_sha256,
                            "edits": [{
                                "old_text": METRIC_PROTOCOL_WORKSPACE_INITIAL_DOCUMENT,
                                "new_text": valid_document,
                            }],
                        },
                    )
                )
            if len(self.requests) == 3:
                return _tool_response(
                    ClientToolCall(
                        "hash-only-commit",
                        METRIC_PROTOCOL_WORKSPACE_COMMIT_TOOL,
                        {"expected_sha256": valid_sha256},
                    )
                )
            raise AssertionError("metric protocol workspace exceeded expected turns")

    backend = TruncatedEditBackend()
    result = _run_metric_protocol_workspace(
        provider=backend,  # type: ignore[arg-type]
        config=ArchitectMetricContractAuthoringConfig(
            model_tier="haiku",
        ),
        request_model=TEST_HAIKU_MODEL,
        user_message="Author one generic protocol.",
        build_validated_packet=build_validated_packet,
        workspace_dir=tmp_path,
        session_id="metric-protocol-truncated-edit",
    )

    assert result.document_content == valid_document
    assert result.loop.history[0]["provider_output_truncated"] is True
    assert result.loop.history[0]["tool_calls"][0]["executed_by_runtime"] is False
    assert result.loop.runtime_executed_tool_calls == 2
    assert (tmp_path / "metric_protocol.json").read_text(
        encoding="utf-8"
    ) == valid_document


def test_metric_protocol_failure_preserves_checkpoint_without_auto_retry() -> None:
    theory_packet_id = "theory_derivation:generic"
    checkpoint = {
        "schema_version": 1,
        "artifact_kind": "MetricProtocolWorkspaceCheckpoint",
        "checkpoint_id": "metric_protocol_workspace_checkpoint:test",
        "session_id": "metric-protocol:test",
        "relative_document_path": "metric_protocol.json",
        "document_sha256": "a" * 64,
        "runtime_edited_content": False,
        "automatic_retry_authorized": False,
        "proof_evidence_status": (
            "METRIC_PROTOCOL_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    result = architect_metric_requirement_validation_failure_result(
        task=AgentTask(
            task_id="architect:metric-workspace-blocked",
            owner_subsystem="ArchitectCoordinator",
            objective="Record one exhausted metric source workspace.",
        ),
        question=_question(),
        architect_context={
            "theory_packet_id": theory_packet_id,
            "architect_metric_protocol_theory_material": {
                "source_theory_packet_id": theory_packet_id,
            },
        },
        blackboard=BlackboardState(
            project_id="metric-workspace-test",
            artifacts={
                theory_packet_id: {
                    "packet_id": theory_packet_id,
                    "artifact_kind": "TheoryDerivationPacket",
                }
            },
        ),
        exc=PacketValidationError(
            validation_label="LLM Architect metric-requirement packet",
            attempts=2,
            errors=["terminal provider failure"],
            history=[],
            recovery_checkpoint=checkpoint,
        ),
    )

    failure = next(iter(result.produced_artifacts.values()))
    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert failure["metric_protocol_workspace_checkpoint_available"] is True
    assert failure["metric_protocol_workspace_checkpoint"] == checkpoint
    assert result.observations[0].payload[
        "metric_protocol_workspace_checkpoint_available"
    ] is True


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


@pytest.mark.parametrize(
    "prior_reviewed_source_hash",
    [None, "revised-theory-hash"],
)
def test_preflight_stops_when_no_prior_finding_closes(
    prior_reviewed_source_hash: str | None,
) -> None:
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
            "review_scope": rejected_packet["review_scope"],
            "review_report": rejected_packet["review_report"],
            "prior_finding_reviews": [
                {
                    "finding_id": finding_id,
                    "status": "UNRESOLVED",
                    "rationale": (
                        "The current parent now covers the bounded branch, but its "
                        "unbounded branch still lacks a current derivation."
                    ),
                    "evidence_refs": ["theory.derivation_steps"],
                    "source_evidence_refs": ["preflight_source_hit:current"],
                }
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

    architect_context = {
        "theory_packet_id": "theory_derivation:generic-revision",
        "architect_metric_protocol_gate": {
            "artifact_kind": "RuntimeArchitectMetricProtocolGate",
            "source_theory_packet_id": "theory_derivation:generic-revision",
            "upstream_theory_revision_count": 1,
            "execution_authorized": False,
        },
    }
    if prior_reviewed_source_hash is not None:
        architect_context["architect_metric_protocol_prior_rejection"] = {
            "artifact_kind": "RuntimeArchitectMetricProtocolPriorRejectionContext",
            "final_review": {
                "source_theory_packet_id": "theory_derivation:generic-revision",
                "source_theory_packet_hash": prior_reviewed_source_hash,
            },
        }

    result = architect_preexecution_metric_protocol_rejection_result(
        task=AgentTask(
            task_id="architect:generic-preflight-stalled",
            owner_subsystem="ArchitectCoordinator",
            objective="Stop a semantically unchanged theory revision.",
        ),
        question=_question(),
        semantic_review_history=history,
        architect_context=architect_context,
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "architect_theory_execution_preflight_stalled"
    )
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["source_theory_lineage_changed"] is False
    assert manifest["preflight_revision_stalled"] is True
    assert manifest["upstream_theory_revision_routed"] is False
    assert manifest["architect_route_requested"] is False
    assert "source_workspace_return_requested" not in manifest
    assert manifest["runtime_selected_owner"] is False


def test_changed_preflight_source_stalls_without_reviewed_finding_progress() -> None:
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
            "review_scope": rejected_packet["review_scope"],
            "review_report": rejected_packet["review_report"],
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
                "progress_made": False,
                "stalled": True,
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
            "architect_metric_protocol_prior_rejection": {
                "artifact_kind": (
                    "RuntimeArchitectMetricProtocolPriorRejectionContext"
                ),
                "final_review": {
                    "source_theory_packet_id": "theory_derivation:prior",
                    "source_theory_packet_hash": "prior-theory-hash",
                },
            },
            "architect_metric_protocol_gate": {
                "artifact_kind": "RuntimeArchitectMetricProtocolGate",
                "source_theory_packet_id": (
                    "theory_derivation:generic-revision"
                ),
                "upstream_theory_revision_count": 1,
                "execution_authorized": False,
            },
        },
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "architect_theory_execution_preflight_stalled"
    )
    manifest = next(iter(result.produced_artifacts.values()))
    assert manifest["prior_finding_progress_made"] is False
    assert manifest["source_theory_lineage_changed"] is True
    assert manifest["preflight_revision_progressed"] is False
    assert manifest["preflight_revision_stalled"] is True
    assert manifest["upstream_theory_revision_routed"] is False
    assert manifest["architect_route_requested"] is False
    assert "source_workspace_return_requested" not in manifest
    assert manifest["runtime_selected_owner"] is False


def test_preflight_progress_can_continue_after_many_revision_rounds() -> None:
    rejected_packet, _backend = _review(accept=False)
    prior_finding_id = rejected_packet["active_unresolved_finding_ids"][0]
    new_finding_id = "theory:newly-discovered-gap"
    history = [
        {
            "revision_index": 8,
            "review_stage": "theory_execution_preflight",
            "source_theory_packet_id": "theory_derivation:round-eight",
            "source_theory_packet_hash": "round-eight-hash",
            "semantic_review_packet_id": rejected_packet["packet_id"],
            "review_report": rejected_packet["review_report"],
            "overall_verdict": "REVISE",
            "prior_finding_reviews": [
                {
                    "finding_id": prior_finding_id,
                    "status": "RESOLVED",
                    "rationale": "The revised document now supplies the argument.",
                    "evidence_refs": ["theory_document:claim"],
                }
            ],
            "findings": [
                {
                    "finding_id": new_finding_id,
                    "severity": "medium",
                    "category": "new_dependency_gap",
                    "summary": "A newly introduced dependent claim needs support.",
                    "observed_behavior": "The dependent claim has no cited step.",
                    "expected_behavior": "The dependency is derived or withdrawn.",
                    "evidence_refs": ["theory_document:new_claim"],
                }
            ],
            "active_unresolved_finding_ids": [new_finding_id],
            "prior_finding_resolution_summary": {
                "prior_active_finding_ids": [prior_finding_id],
                "resolved_prior_finding_ids": [prior_finding_id],
                "still_unresolved_prior_finding_ids": [],
                "new_finding_ids": [new_finding_id],
                "progress_made": True,
                "stalled": False,
            },
        }
    ]

    result = architect_preexecution_metric_protocol_rejection_result(
        task=AgentTask(
            task_id="architect:progressive-round-eight",
            owner_subsystem="ArchitectCoordinator",
            objective="Continue a progressing theory lineage.",
        ),
        question=_question(),
        semantic_review_history=history,
        architect_context={
            "theory_packet_id": "theory_derivation:round-eight",
            "architect_metric_protocol_gate": {
                "artifact_kind": "RuntimeArchitectMetricProtocolGate",
                "source_theory_packet_id": "theory_derivation:round-eight",
                "upstream_theory_revision_count": 8,
                "execution_authorized": False,
            },
        },
    )

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "TheoryDeveloper"
    assert result.next_task.budget[RUNTIME_CONTINUATION_BUDGET_MARKER_KEY] == {
        "scope": "workspace_continuation",
        "parent_task_id": "architect:progressive-round-eight",
        "next_task_id": result.next_task.task_id,
        "parent_owner_subsystem": "ArchitectCoordinator",
        "owner_subsystem": "TheoryDeveloper",
    }
    feedback = result.next_task.inputs["environment_feedback"]
    assert feedback["upstream_theory_revision_count"] == 9
    assert feedback["continuation_budget_authority"] == (
        "AgentRuntime.max_iterations"
    )
    assert feedback["review_document_ref"] == rejected_packet["review_report"]
    progress = result.next_task.inputs["architect_context"][
        "runtime_theory_revision_progress"
    ]
    assert progress == {
        "revisions_used": 9,
        "continuation_budget_authority": "AgentRuntime.max_iterations",
        "reset_scope": "fresh_question_runtime_only",
    }

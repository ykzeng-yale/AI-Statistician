from __future__ import annotations

import json

from ai_statistician.fingerprint import stable_hash
from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.lean_candidate_revision_tool_loop import (
    run_lean_candidate_revision_tool_loop,
)
from ai_statistician.lean_candidate_identity import (
    TRUSTED_LEAN_AXIOMS,
    _lean_axioms_from_report,
)
from ai_statistician.llm_json_repair import PacketValidationError
from ai_statistician.model_backend import (
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
)
from ai_statistician.formalizer_llm import (
    FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
    FormalizerConfig,
    LLMFormalizerProofEngineerAgent,
)
from ai_statistician.research_schema import OpenResearchQuestion
import ai_statistician.formalizer_llm as formalizer_module
import ai_statistician.research_agent_runtime as runtime_module


class ScriptedLeanToolBackend:
    provider_name = "anthropic"

    def __init__(self, responses: list[ClientToolTurnResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[ClientToolTurnRequest] = []

    def generate_client_tool_turn(
        self,
        request: ClientToolTurnRequest,
    ) -> ClientToolTurnResponse:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("ScriptedLeanToolBackend exhausted")
        return self.responses.pop(0)


def _response(*calls: ClientToolCall) -> ClientToolTurnResponse:
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
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        metadata={
            "client_tool_transport": True,
            "tools_executed_by_backend": False,
            "provider_stop_reason": "tool_use",
            "provider_usage": {"input_tokens": 17, "output_tokens": 5},
        },
    )


def test_lean_axiom_audit_uses_lean_report_instead_of_source_grammar() -> None:
    checked, names = _lean_axioms_from_report(
        "'target' depends on axioms: [propext, Classical.choice]"
    )
    assert checked is True
    assert names == ("propext", "Classical.choice")
    assert set(names) <= TRUSTED_LEAN_AXIOMS

    checked, names = _lean_axioms_from_report(
        "'target' depends on axioms: [project.generatedAxiom]"
    )
    assert checked is True
    assert names == ("project.generatedAxiom",)
    assert set(names) - TRUSTED_LEAN_AXIOMS == {"project.generatedAxiom"}

    assert _lean_axioms_from_report(
        "'target' does not depend on any axioms"
    ) == (True, ())
    assert _lean_axioms_from_report("unrelated compiler output") == (False, ())


def test_lean_candidate_tool_loop_keeps_code_model_owned_and_compiler_bound() -> None:
    initial = "import Missing.Module\n\ntheorem target : True := by trivial\n"
    repaired = "import Mathlib.Data.Nat.Basic\n\ntheorem target : True := by trivial\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "search-1",
                    "search_formal_environment",
                    {"query": "True.intro declaration", "max_results": 3},
                )
            ),
            _response(
                ClientToolCall(
                    "edit-1",
                    "replace_lean_source",
                    {"lean_source": repaired},
                ),
                ClientToolCall("check-1", "check_lean_source", {}),
            ),
            _response(
                ClientToolCall("submit-1", "submit_compiled_source", {})
            ),
        ]
    )
    checked_sources: list[str] = []
    searches: list[tuple[str, int]] = []

    def check(source: str):
        checked_sources.append(source)
        compiled = source == repaired
        return {
            "source_hash": stable_hash(source),
            "compiled": compiled,
            "local_lean_attempted": True,
            "local_lean_stderr": "" if compiled else "unknown module",
        }

    def search(query: str, k: int):
        searches.append((query, k))
        return {
            "query": query,
            "hits": [
                {
                    "module": "Mathlib.Data.Nat.Basic",
                    "name": "True.intro",
                }
            ],
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Repair this target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_source_updates=2,
        max_searches=2,
        max_checks=2,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=search,
    )

    assert result.lean_source == repaired
    assert result.source_hash == stable_hash(repaired)
    assert checked_sources == [repaired]
    assert searches == [("True.intro declaration", 3)]
    assert result.evidence["runtime_selected_lean_code"] is False
    assert result.evidence["model_owned_lean_code"] is True
    assert result.evidence["runtime_executed_tool_calls"] == 4
    assert result.evidence["local_lean_checks"] == 1
    assert result.evidence["formal_environment_searches"] == 1
    assert result.evidence["model"] == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    assert all(
        request.model == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
        for request in backend.requests
    )
    assert set(tool.name for tool in backend.requests[0].tools) == {
        "replace_lean_source",
        "search_formal_environment",
        "check_lean_source",
        "submit_compiled_source",
    }


def test_lean_candidate_tool_loop_rejects_submit_after_unchecked_edit() -> None:
    initial = "theorem target : True := by trivial\n"
    revised = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(ClientToolCall("check-0", "check_lean_source", {})),
            _response(
                ClientToolCall(
                    "edit-1",
                    "replace_lean_source",
                    {"lean_source": revised},
                ),
                ClientToolCall("submit-stale", "submit_compiled_source", {}),
            ),
            _response(
                ClientToolCall("check-1", "check_lean_source", {}),
                ClientToolCall("submit-1", "submit_compiled_source", {}),
            ),
        ]
    )

    def check(source: str):
        return {"source_hash": stable_hash(source), "compiled": True}

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Repair this target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_source_updates=2,
        max_searches=1,
        max_checks=2,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
    )

    assert result.lean_source == revised
    stale_submit = backend.requests[2].messages[-1]["content"][-1]
    assert stale_submit["is_error"] is True
    assert "current_source_has_no_successful_local_lean_check" in stale_submit[
        "content"
    ]
    assert result.evidence["local_lean_checks"] == 2


def test_lean_candidate_tool_loop_stops_repeated_identical_checks() -> None:
    source = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(ClientToolCall("check-1", "check_lean_source", {})),
            _response(ClientToolCall("check-2", "check_lean_source", {})),
        ]
    )

    try:
        run_lean_candidate_revision_tool_loop(
            provider=backend,
            system_prompt="Use tools.",
            user_prompt="Repair this target.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=3,
            max_source_updates=1,
            max_searches=1,
            max_checks=3,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=source,
            check_candidate=lambda current: {
                "source_hash": stable_hash(current),
                "compiled": False,
                "local_lean_stderr": "same compiler diagnostic",
            },
            search_formal_environment=lambda query, k: [],
        )
    except PacketValidationError as exc:
        assert "no new progress" in " ".join(exc.errors)
    else:
        raise AssertionError("repeated identical Lean checks did not stop")


def test_lean_candidate_tool_loop_does_not_hide_a_check_at_turn_budget() -> None:
    initial = "theorem target : True := by exact True.intro\n"
    repaired = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(ClientToolCall("check-initial", "check_lean_source", {})),
            _response(
                ClientToolCall(
                    "edit-final",
                    "replace_lean_source",
                    {"lean_source": repaired},
                )
            ),
        ]
    )
    checked_sources: list[str] = []

    def check(source: str):
        checked_sources.append(source)
        return {
            "source_hash": stable_hash(source),
            "compiled": source == repaired,
            "local_lean_stderr": "" if source == repaired else "initial failure",
        }

    try:
        run_lean_candidate_revision_tool_loop(
            provider=backend,
            system_prompt="Use tools.",
            user_prompt="Revise this target.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=2,
            max_source_updates=1,
            max_searches=1,
            max_checks=2,
            max_no_progress_turns=2,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=initial,
            check_candidate=check,
            search_formal_environment=lambda query, k: [],
        )
    except PacketValidationError as exc:
        checkpoint = exc.recovery_checkpoint
        assert checkpoint is not None
        assert checkpoint["current_source"] == repaired
        assert checkpoint["last_check"] == {}
        assert "final_runtime_check_performed" not in checkpoint
    else:
        raise AssertionError("unsubmitted final source was accepted")

    assert checked_sources == [initial]


def test_lean_candidate_tool_loop_preserves_uncompiled_latest_edit_checkpoint() -> None:
    initial = "theorem target : True := by exact True.intro\n"
    latest = "theorem target : False := by exact False.elim (by contradiction)\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "edit-final",
                    "replace_lean_source",
                    {"lean_source": latest},
                )
            )
        ]
    )

    try:
        run_lean_candidate_revision_tool_loop(
            provider=backend,
            system_prompt="Use tools.",
            user_prompt="Repair this target.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_source_updates=1,
            max_searches=1,
            max_checks=1,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=initial,
            check_candidate=lambda source: {
                "source_hash": stable_hash(source),
                "compiled": False,
                "local_lean_stderr": "type mismatch",
            },
            search_formal_environment=lambda query, k: [],
        )
    except PacketValidationError as exc:
        checkpoint = exc.recovery_checkpoint
        assert checkpoint is not None
        assert checkpoint["artifact_kind"] == (
            "LeanCandidateRevisionRecoveryCheckpoint"
        )
        assert checkpoint["current_source"] == latest
        assert checkpoint["current_source_hash"] == stable_hash(latest)
        assert checkpoint["last_check"] == {}
        assert "final_runtime_check_performed" not in checkpoint
        assert checkpoint["model_owned_lean_code"] is True
        assert checkpoint["kernel_verified"] is False
    else:
        raise AssertionError("uncompiled final source was not checkpointed")


def test_lean_candidate_prompt_keeps_complete_source_and_verifier_observation() -> None:
    exact_error = (
        "type mismatch\n"
        + "x" * 4000
        + "EXACT_MIDDLE_LEAN_OBSERVATION"
        + "y" * 4000
    )
    initial_source = "theorem target : True := by\n  exact True.intro\n"
    prompt = formalizer_module._build_lean_candidate_revision_tool_prompt(
        question=OpenResearchQuestion(
            id="compact-context",
            title="Compact Lean context",
            description="Keep exact target context and retrieve signatures on demand.",
        ),
        parent_packet={"packet_id": "formalizer_proposal:compact"},
        candidate_id="target-candidate",
        candidate_source_field="formal_targets",
        candidate_lean_declaration="target",
        initial_source=initial_source,
        environment_feedback={
            "feedback_type": "formal_target_semantic_review_feedback",
            "overall_verdict": "ACCEPT",
            "candidate_id": "target-candidate",
            "proofengineer_repair_context": {
                "target_lean_declaration": "target",
                "target_theorem_statement": "theorem target : True",
                "target_theorem_statement_hash": "target-hash",
                "formalizer_candidate_semantic_review_status": (
                    "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
                ),
                "proof_state_trace_rag": {"hits": ["x" * 30000]},
                "candidate_rerun_specs": ["y" * 30000],
                "formal_source_grounding_hits": [{"hits": ["z" * 30000]}],
            },
            "reviewed_source_artifacts": [
                {"exact_source_code": "duplicate" * 5000}
            ],
            "candidate_diagnostics": [
                {
                    "candidate_id": "target-candidate",
                    "source_hash": "candidate-hash",
                    "lean_source_excerpt": "duplicate" * 5000,
                    "local_lean_stderr": exact_error,
                }
            ],
        },
    )

    payload = json.loads(prompt)
    assert payload["current_lean_source"] == initial_source
    feedback = payload["runtime_observations"]
    context = feedback["target_and_environment_observations"]
    assert context["target_theorem_statement"] == "theorem target : True"
    assert "proof_state_trace_rag" in context
    assert "formal_source_grounding_hits" in context
    assert context["candidate_rerun_specs"] == ["y" * 30000]
    assert feedback["reviewed_source_artifacts"] == [
        {"exact_source_code": "duplicate" * 5000}
    ]
    observation = feedback["candidate_diagnostics"][0]
    assert observation["lean_source_excerpt"] == "duplicate" * 5000
    assert observation["local_lean_stderr"] == exact_error
    assert "EXACT_MIDDLE_LEAN_OBSERVATION" in prompt
    assert "proofengineer_repair_context" not in feedback
    assert "required_repair" not in prompt
    assert "recommended_repair" not in prompt


def test_formalizer_validation_failure_routes_model_source_checkpoint() -> None:
    latest = "theorem target : True := by\n  exact True.intro\n"
    checkpoint = {
        "schema_version": 1,
        "artifact_kind": "LeanCandidateRevisionRecoveryCheckpoint",
        "candidate_id": "target-candidate",
        "candidate_lean_declaration": "target",
        "parent_source_hash": "parent-hash",
        "current_source_hash": stable_hash(latest),
        "current_source": latest,
        "last_check": {
            "source_hash": stable_hash(latest),
            "compiled": False,
            "local_lean_stderr": "type mismatch",
        },
        "model_owned_lean_code": True,
        "runtime_selected_lean_code": False,
        "kernel_verified": False,
        "proof_evidence_status": (
            "CLIENT_TOOL_REPAIR_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    question = OpenResearchQuestion(
        id="checkpoint-routing",
        title="Route model source checkpoint",
        description="Preserve the latest model candidate across bounded repair tasks.",
    )
    result = runtime_module._formalizer_packet_validation_failure_result(
        task=AgentTask(
            task_id="formalize:checkpoint-routing",
            owner_subsystem="FormalizationEvaluator",
            objective="Continue the bounded model repair.",
            inputs={"environment_feedback": {}},
        ),
        question=question,
        theory_packet_id="theory:checkpoint",
        simulation_manifest_id="simulation:checkpoint",
        algorithm_sandbox_manifest_id="algorithm:checkpoint",
        proof_bank_runtime_memory_summary={},
        exc=PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool revision",
            attempts=2,
            errors=["global client-tool turn budget exhausted"],
            history=[],
            recovery_checkpoint=checkpoint,
        ),
    )

    assert result.next_task is not None
    routed = result.next_task.inputs["environment_feedback"][
        "formalizer_recovery_checkpoint"
    ]
    assert routed == checkpoint
    failure = next(iter(result.produced_artifacts.values()))
    assert failure["formalizer_recovery_checkpoint"]["current_source"] == latest
    assert failure["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")


def test_runtime_client_tool_revision_requires_independent_target_acceptance(
    tmp_path,
    monkeypatch,
) -> None:
    source = "theorem target : True := by exact True.intro\n"
    artifact_path = tmp_path / "parent.lean"
    artifact_path.write_text(source, encoding="utf-8")
    parent_packet_id = "formalizer_proposal:parent"
    materialization_id = "formalizer_lean_candidate_materialization:parent"
    candidate_id = "target-candidate"
    target_statement = "True"
    target_statement_hash = runtime_module._external_exact_target_statement_hash(
        target_statement
    )
    parent_packet = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": parent_packet_id,
    }
    materialization = {
        "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
        "manifest_id": materialization_id,
        "source_formalizer_packet_id": parent_packet_id,
        "candidate_rows": [
            {
                "candidate_id": candidate_id,
                "candidate_lean_declaration": "target",
                "source_field": "formal_targets",
                "artifact_path": str(artifact_path),
                "source_hash": stable_hash(source),
                "candidate_metadata": {},
            }
        ],
    }
    review_packet_id = "formal_target_semantic_review:accepted"
    review_packet = {
        "artifact_kind": "FormalTargetSemanticReviewPacket",
        "packet_id": review_packet_id,
        "question_id": "q",
        "overall_verdict": "ACCEPT",
        "candidate_materialization_id": materialization_id,
        "candidate_materialization_hash": stable_hash(materialization),
        "proposal_packet_id": parent_packet_id,
        "proposal_packet_hash": stable_hash(parent_packet),
        "candidate_id": candidate_id,
        "candidate_source_hash": stable_hash(source),
        "target_theorem_statement_hash": target_statement_hash,
    }
    review_packet_hash = stable_hash(review_packet)
    review_execution_id = "formal_target_semantic_review_execution:accepted"
    review_execution = {
        "artifact_kind": "RuntimeFormalTargetSemanticReviewExecutionManifest",
        "execution_id": review_execution_id,
        "question_id": "q",
        "candidate_materialization_id": materialization_id,
        "candidate_id": candidate_id,
        "candidate_source_hash": stable_hash(source),
        "review_packet_id": review_packet_id,
        "review_packet_hash": review_packet_hash,
        "overall_verdict": "ACCEPT",
        "semantic_review_accepted": True,
    }
    blackboard = BlackboardState(
        project_id="lean-client-tool-runtime",
        artifacts={
            parent_packet_id: parent_packet,
            materialization_id: materialization,
            review_packet_id: review_packet,
            review_execution_id: review_execution,
        },
    )
    task = AgentTask(
        task_id="formal-target-review-accepted:q:1234",
        owner_subsystem="ProofEngineer",
        objective="Repair exact candidate.",
    )
    question = OpenResearchQuestion(
        id="q",
        title="Runtime client-tool repair",
        description="Exercise accepted target routing.",
    )
    feedback = {
        "candidate_materialization_id": materialization_id,
        "candidate_id": candidate_id,
        "candidate_source_hash": stable_hash(source),
        "semantic_review_execution_id": review_execution_id,
        "semantic_review_packet_id": review_packet_id,
        "semantic_review_packet_hash": review_packet_hash,
        "overall_verdict": "ACCEPT",
        "proofengineer_repair_context": {
            "formalizer_candidate_semantic_review_status": (
                "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
            ),
            "candidate_artifact_path": str(artifact_path),
            "lineage_candidate_artifact_hash": stable_hash(source),
            "target_lean_declaration": "target",
            "target_theorem_statement": target_statement,
            "target_theorem_statement_hash": target_statement_hash,
            "target_theorem_statement_hash_algorithm": (
                runtime_module.EXACT_TARGET_STATEMENT_HASH_ALGORITHM
            ),
            "formalizer_candidate_semantic_review_execution_id": (
                review_execution_id
            ),
            "formalizer_candidate_semantic_review_packet_id": review_packet_id,
            "formalizer_candidate_semantic_review_packet_hash": (
                review_packet_hash
            ),
            "formalizer_candidate_semantic_review_candidate_source_hash": (
                stable_hash(source)
            ),
            "formalizer_candidate_semantic_review_target_statement_hash": (
                target_statement_hash
            ),
            "formalizer_candidate_semantic_review_target_statement_hash_algorithm": (
                runtime_module.EXACT_TARGET_STATEMENT_HASH_ALGORITHM
            ),
        },
    }

    class FakeConfig:
        use_client_tool_lean_candidate_revision = True

    class FakeProvider:
        def generate_client_tool_turn(self, request):
            raise AssertionError("fake agent owns the isolated method call")

    class FakeAgent:
        config = FakeConfig()
        provider = FakeProvider()

        def __init__(self) -> None:
            self.check_result = {}
            self.search_result = {}

        def revise_lean_candidate_with_client_tools(self, **kwargs):
            assert kwargs["candidate_id"] == candidate_id
            assert kwargs["initial_source"] == source
            self.check_result = dict(kwargs["check_candidate"](source))
            self.search_result = kwargs["search_formal_environment"](
                "target declaration",
                3,
            )
            return (
                {"packet_id": "formalizer_proposal:repaired"},
                {
                    "artifact_kind": "LeanCandidateRevisionClientToolLoop",
                    "candidate_id": candidate_id,
                    "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
                    "model_tier": "haiku",
                    "submitted_source_hash": stable_hash(source),
                    "runtime_executed_tool_calls": 2,
                    "proof_evidence_status": (
                        "LEAN_CANDIDATE_CLIENT_TOOL_LOOP_RECORDED_NOT_PROOF_EVIDENCE"
                    ),
                },
            )

    monkeypatch.setattr(
        runtime_module,
        "_formalizer_lean_candidate_precheck_errors",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        runtime_module,
        "_run_formalizer_lean_candidate_local_check",
        lambda **kwargs: {
            "local_lean_attempted": True,
            "local_lean_compiled": True,
            "local_lean_source_compiled": True,
            "local_lean_exit_status": "0",
            "local_lean_stdout": "target : True",
            "local_lean_stderr": "",
            "candidate_identity_lean_checked": True,
            "candidate_identity_lean_verified": True,
        },
    )
    agent = FakeAgent()
    result = runtime_module._runtime_formalizer_lean_candidate_client_tool_revision(
        proposal_agent=agent,
        question=question,
        task=task,
        blackboard=blackboard,
        theory_packet={},
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
        formal_source_retriever=None,
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=tmp_path,
        lean_candidate_lean_timeout=5,
    )

    assert result is not None
    packet, evidence = result
    assert packet["packet_id"] == "formalizer_proposal:repaired"
    assert agent.check_result["compiled"] is True
    assert agent.check_result["source_hash"] == stable_hash(source)
    assert agent.search_result["retrieval_status"] == (
        "formal_source_retriever_unavailable"
    )
    assert evidence["parent_materialization_manifest_id"] == materialization_id
    assert evidence["parent_formalizer_packet_id"] == parent_packet_id
    assert evidence["model"] == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL

    monkeypatch.setattr(
        runtime_module,
        "_proofengineer_formal_source_grounding_hit_groups",
        lambda *args, **kwargs: [
            {
                "query": "target declaration",
                "query_role": "model_selected_lean_repair_query",
                "hits": [
                    {
                        "source_id": "active-project",
                        "path": "/tmp/Target.lean",
                        "line": 7,
                        "name": "Target.support",
                        "signature": "Target.support (h : True) : True",
                        "documentation": "large provenance " * 5000,
                    }
                ],
            }
        ],
    )
    compact_agent = FakeAgent()
    compact_result = runtime_module._runtime_formalizer_lean_candidate_client_tool_revision(
        proposal_agent=compact_agent,
        question=question,
        task=task,
        blackboard=blackboard,
        theory_packet={},
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
        formal_source_retriever=object(),
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=tmp_path,
        lean_candidate_lean_timeout=5,
    )
    assert compact_result is not None
    assert compact_agent.search_result["retrieval_status"] == (
        "prompt_safe_signature_hits"
    )
    assert compact_agent.search_result["hits"][0]["signature"] == (
        "Target.support (h : True) : True"
    )
    assert "documentation" not in compact_agent.search_result["hits"][0]
    assert len(json.dumps(compact_agent.search_result)) < 5600

    rejected = runtime_module._runtime_formalizer_lean_candidate_client_tool_revision(
        proposal_agent=agent,
        question=question,
        task=task,
        blackboard=blackboard,
        theory_packet={},
        environment_feedback={**feedback, "overall_verdict": "REVISE"},
        proof_bank_runtime_memory_summary={},
        formal_source_retriever=None,
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=tmp_path,
        lean_candidate_lean_timeout=5,
    )
    assert rejected is None

    blackboard.artifacts[review_packet_id] = {
        **review_packet,
        "candidate_source_hash": "tampered",
    }
    try:
        runtime_module._runtime_formalizer_lean_candidate_client_tool_revision(
            proposal_agent=agent,
            question=question,
            task=task,
            blackboard=blackboard,
            theory_packet={},
            environment_feedback=feedback,
            proof_bank_runtime_memory_summary={},
            formal_source_retriever=None,
            lean_candidate_root=tmp_path / "candidates",
            lean_candidate_local_lean=True,
            lean_candidate_lean_project=tmp_path,
            lean_candidate_lean_timeout=5,
        )
    except PacketValidationError as exc:
        assert exc.validation_label == (
            "Formalizer Lean candidate accepted-review lineage"
        )
    else:
        raise AssertionError("tampered accepted review lineage was not rejected")


def test_formalizer_client_tool_revision_rebuilds_only_bound_candidate_source(
    monkeypatch,
) -> None:
    original = "import Missing.Module\n\ntheorem target : True := by trivial\n"
    repaired = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "edit",
                    "replace_lean_source",
                    {"lean_source": repaired},
                ),
                ClientToolCall("check", "check_lean_source", {}),
            ),
            _response(
                ClientToolCall("submit", "submit_compiled_source", {})
            ),
        ]
    )
    agent = LLMFormalizerProofEngineerAgent(
        provider=backend,
        config=FormalizerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
        ),
    )
    for name in (
        "validate_formalizer_packet",
        "_validate_indexed_lean_environment_candidate_bindings",
        "_validate_capability_eval_formalizer_lean_candidate_packet",
    ):
        monkeypatch.setattr(formalizer_module, name, lambda *args, **kwargs: [])
    question = OpenResearchQuestion(
        id="q",
        title="Bound source replacement",
        description="Replace only one independently reviewed Lean candidate.",
    )
    parent_packet = {
        "schema_version": 1,
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer_proposal:parent",
        "provider": "anthropic",
        "backend_provider": "anthropic",
        "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "model_tier": "haiku",
        "formal_targets": [
            {
                "id": "target-candidate",
                "formal_target_role": (
                    FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE
                ),
                "candidate_lean_declaration": "target",
                "lean_statement_sketch": original,
                "lean_imports": ["Missing.Module"],
                "expected_status": "NEEDS_KERNEL_CHECK",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "target",
                },
            },
            {
                "id": "untouched-helper",
                "formal_target_role": "HELPER_OR_SUPPORT",
                "candidate_lean_declaration": "helper",
                "lean_statement_sketch": (
                    "theorem helper : True := by exact True.intro\n"
                ),
                "lean_imports": [],
                "expected_status": "NEEDS_KERNEL_CHECK",
            },
        ],
        "lemma_dependency_plan": [],
        "retrieval_queries": [],
        "proof_search_plan": {},
        "proof_bank_obligation_requests": [],
        "gap_taxonomy": [],
        "critic_findings": [],
        "next_actions": [],
    }
    feedback = {
        "overall_verdict": "ACCEPT",
        "proofengineer_repair_context": {
            "formalizer_candidate_semantic_review_status": (
                "INDEPENDENT_SEMANTIC_REVIEW_ACCEPTED_NOT_PROOF_EVIDENCE"
            )
        },
    }

    packet, evidence = agent.revise_lean_candidate_with_client_tools(
        question=question,
        theory_packet={},
        parent_packet=parent_packet,
        candidate_id="target-candidate",
        candidate_source_field="formal_targets",
        candidate_lean_declaration="target",
        initial_source=original,
        environment_feedback=feedback,
        proof_bank_runtime_memory_summary={},
        check_candidate=lambda source: {
            "source_hash": stable_hash(source),
            "compiled": source == repaired,
        },
        search_formal_environment=lambda query, k: [],
    )

    targets = {row["id"]: row for row in packet["formal_targets"]}
    assert targets["target-candidate"]["lean_statement_sketch"] == repaired
    assert targets["target-candidate"]["lean_imports"] == []
    untouched = targets["untouched-helper"]
    parent_untouched = parent_packet["formal_targets"][1]
    for field in (
        "id",
        "formal_target_role",
        "candidate_lean_declaration",
        "lean_statement_sketch",
        "lean_imports",
        "expected_status",
    ):
        assert untouched[field] == parent_untouched[field]
    assert packet["packet_id"] != parent_packet["packet_id"]
    assert packet["model"] == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    assert evidence["runtime_selected_lean_code"] is False

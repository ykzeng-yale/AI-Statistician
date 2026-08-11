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
from ai_statistician.structured_output_retry import PacketValidationError
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
    assert result.evidence["runtime_executed_tool_calls"] == 3
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
    }
    assert all(request.disable_parallel_tool_use for request in backend.requests)
    assert result.evidence["handoff_mode"] == (
        "successful_model_requested_check"
    )
    assert result.evidence["model_explicit_submit"] is False


def test_prover_candidates_are_observations_and_only_model_replaces_source() -> None:
    initial = "theorem target : True := by\n  sorry\n"
    model_source = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "prove-1",
                    "search_proof_candidates",
                    {"query": "close target from current goal", "max_results": 2},
                )
            ),
            _response(
                ClientToolCall(
                    "edit-1",
                    "replace_lean_source",
                    {"lean_source": model_source},
                ),
                ClientToolCall("check-1", "check_lean_source", {}),
            ),
        ]
    )
    proof_search_calls: list[tuple[str, str, int, dict]] = []
    checked_sources: list[str] = []

    def search(source: str, query: str, k: int, last_check):
        proof_search_calls.append((source, query, k, dict(last_check)))
        return {
            "candidates": [{"candidate_proof_body": "by exact True.intro"}],
            "provider": "openprover",
        }

    def check(source: str):
        checked_sources.append(source)
        return {"source_hash": stable_hash(source), "compiled": source == model_source}

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Prove this target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_source_updates=1,
        max_searches=1,
        max_proof_searches=1,
        max_checks=1,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        search_proof_candidates=search,
    )

    assert proof_search_calls == [
        (initial, "close target from current goal", 2, {})
    ]
    assert checked_sources == [model_source]
    assert result.lean_source == model_source
    assert result.evidence["proof_candidate_searches"] == 1
    assert result.evidence["runtime_selected_lean_code"] is False
    assert result.evidence["model_owned_lean_code"] is True
    assert "search_proof_candidates" in result.evidence["tool_names"]


def test_model_selects_lean_state_inspection_inside_same_source_loop() -> None:
    initial = "theorem target : True := by\n  exact missing\n"
    revised = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(ClientToolCall("check-1", "check_lean_source", {})),
            _response(ClientToolCall("state-1", "inspect_lean_state", {})),
            _response(
                ClientToolCall(
                    "edit-1",
                    "replace_lean_source",
                    {"lean_source": revised},
                ),
                ClientToolCall("check-2", "check_lean_source", {}),
            ),
        ]
    )
    inspections: list[tuple[str, dict]] = []

    def check(source: str):
        compiled = source == revised
        return {
            "source_hash": stable_hash(source),
            "compiled": compiled,
            "local_lean_stderr": "unknown identifier 'missing'" if not compiled else "",
        }

    def inspect(source: str, last_check):
        inspections.append((source, dict(last_check)))
        return {
            "provider": "lean_lsp_mcp",
            "goals": ["|- True"],
            "executed_tools": ["lean_lsp_mcp.lean_goal"],
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Inspect and revise the exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_source_updates=1,
        max_searches=1,
        max_state_inspections=1,
        max_checks=2,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        inspect_lean_state=inspect,
    )

    assert inspections[0][0] == initial
    assert inspections[0][1]["source_hash"] == stable_hash(initial)
    assert result.lean_source == revised
    assert result.evidence["lean_state_inspections"] == 1
    assert "inspect_lean_state" in result.evidence["tool_names"]
    assert "inspect_lean_state" not in {
        tool.name for tool in backend.requests[0].tools
    }
    assert "inspect_lean_state" in {
        tool.name for tool in backend.requests[1].tools
    }


def test_lean_candidate_tool_loop_hides_exhausted_actions_before_next_turn() -> None:
    initial = "import Missing.Module\n\ntheorem target : True := by trivial\n"
    revised = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "search-1",
                    "search_formal_environment",
                    {"query": "True introduction"},
                )
            ),
            _response(
                ClientToolCall(
                    "replace-1",
                    "replace_lean_source",
                    {"lean_source": revised},
                )
            ),
            _response(ClientToolCall("check-1", "check_lean_source", {})),
        ]
    )

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise this target from environment observations.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_source_updates=1,
        max_searches=1,
        max_checks=1,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=lambda source: {
            "source_hash": stable_hash(source),
            "compiled": source == revised,
        },
        search_formal_environment=lambda query, k: {
            "query": query,
            "hits": [{"module": "Mathlib", "name": "True.intro"}],
        },
    )

    assert result.lean_source == revised
    assert [tool.name for tool in backend.requests[1].tools] == [
        "replace_lean_source",
        "check_lean_source",
    ]
    assert [tool.name for tool in backend.requests[2].tools] == [
        "check_lean_source"
    ]
    assert backend.requests[2].tool_choice == "check_lean_source"
    assert all(request.disable_parallel_tool_use for request in backend.requests)


def test_lean_candidate_tool_loop_hands_off_on_successful_requested_check() -> None:
    initial = "theorem target : True := by trivial\n"
    revised = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "edit-1",
                    "replace_lean_source",
                    {"lean_source": revised},
                ),
                ClientToolCall("check-1", "check_lean_source", {}),
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
    assert len(backend.requests) == 1
    assert result.evidence["local_lean_checks"] == 1
    assert result.evidence["handoff_mode"] == (
        "successful_model_requested_check"
    )


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
        assert checkpoint["latest_check_observation"]["source_hash"] == (
            stable_hash(initial)
        )
        assert checkpoint["parent_source_hash"] == stable_hash(initial)
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
        assert checkpoint["latest_check_observation"] == {}
        assert checkpoint["parent_source_hash"] == stable_hash(initial)
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
            "formalizer_workspace_context": {
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
            "formalizer_recovery_checkpoint": {
                "artifact_kind": "LeanCandidateRevisionRecoveryCheckpoint",
                "candidate_id": "target-candidate",
                "candidate_lean_declaration": "target",
                "current_source_hash": stable_hash(initial_source),
                "current_source": initial_source,
                "model_owned_lean_code": True,
                "runtime_selected_lean_code": False,
                "kernel_verified": False,
            },
        },
    )

    payload = json.loads(prompt)
    assert payload["current_lean_source"] == initial_source
    feedback = payload["runtime_observations"]
    context = feedback["target_and_environment_observations"]
    assert context["target_theorem_statement"] == "theorem target : True"
    assert "proof_state_trace_rag" not in context
    assert "formal_source_grounding_hits" not in context
    assert "candidate_rerun_specs" not in context
    assert "reviewed_source_artifacts" not in feedback
    observation = feedback["candidate_diagnostics"][0]
    assert "lean_source_excerpt" not in observation
    assert observation["local_lean_stderr"] == exact_error
    checkpoint = feedback["model_revision_checkpoint"]
    assert checkpoint["current_source_hash"] == stable_hash(initial_source)
    assert "current_source" not in checkpoint
    assert "EXACT_MIDDLE_LEAN_OBSERVATION" in prompt
    assert "formalizer_workspace_context" not in feedback
    assert "required_repair" not in prompt
    assert "recommended_repair" not in prompt
    assert len(prompt) < 20000


def test_formalizer_validation_failure_continues_same_workspace_once() -> None:
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
            "CLIENT_TOOL_ITERATION_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    question = OpenResearchQuestion(
        id="checkpoint-routing",
        title="Route model source checkpoint",
        description="Preserve the latest model candidate after a bounded tool loop.",
    )
    result = runtime_module._formalizer_packet_validation_failure_result(
        task=AgentTask(
            task_id="formalize:checkpoint-routing",
            owner_subsystem="FormalizationEvaluator",
            objective="Run the bounded model-owned Lean workspace.",
            inputs={"environment_feedback": {}},
        ),
        question=question,
        theory_packet_id="theory:checkpoint",
        simulation_manifest_id="simulation:checkpoint",
        algorithm_sandbox_manifest_id="algorithm:checkpoint",
        exc=PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool revision",
            attempts=2,
            errors=["global client-tool turn budget exhausted"],
            history=[],
            recovery_checkpoint=checkpoint,
        ),
    )

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "FormalizationEvaluator"
    assert result.next_task.task_id.startswith("formalizer-workspace-continuation:")
    failure = next(iter(result.produced_artifacts.values()))
    routed = result.next_task.inputs["environment_feedback"]
    assert routed["artifact_kind"] == "RuntimeWorkspaceObservationRef"
    assert routed["source_artifact_id"] == failure["failure_id"]
    assert routed["source_artifact_hash"] == stable_hash(failure)
    assert "formalizer_recovery_checkpoint" not in routed
    assert result.next_task.inputs["formalizer_workspace_continuation_attempt"] == 1
    assert failure["formalizer_recovery_checkpoint"]["current_source"] == latest
    assert failure["rejected_candidate_complete"] is False
    assert failure["complete_current_source_checkpoint_provided"] is True
    assert failure["validation_boundary"][
        "complete_rejected_candidate_provided"
    ] is False
    assert failure["validation_boundary"][
        "complete_current_source_checkpoint_provided"
    ] is True
    assert "same Formalizer" in result.rationale
    assert failure["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")

    exhausted = runtime_module._formalizer_packet_validation_failure_result(
        task=result.next_task,
        question=question,
        theory_packet_id="theory:checkpoint",
        simulation_manifest_id="simulation:checkpoint",
        algorithm_sandbox_manifest_id="algorithm:checkpoint",
        exc=PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool revision",
            attempts=2,
            errors=["global client-tool turn budget exhausted"],
            history=[],
            recovery_checkpoint=checkpoint,
        ),
    )

    assert exhausted.status == "BLOCKED"
    assert exhausted.next_task is None
    assert exhausted.failure_classification == (
        "formalizer_workspace_continuation_exhausted"
    )
    assert "Architect or Critic" in exhausted.rationale


def test_formalizer_workspace_hydrates_observation_ref_before_source_loop(
    monkeypatch,
) -> None:
    question = OpenResearchQuestion(
        id="hydrate-formalizer-checkpoint",
        title="Hydrate a Formalizer checkpoint",
        description="Resume exact model-owned source from the artifact store.",
    )
    source_artifact_id = "formalizer_validation_failure:checkpoint"
    checkpoint = {
        "schema_version": 1,
        "artifact_kind": "LeanCandidateRevisionRecoveryCheckpoint",
        "candidate_id": "target-candidate",
        "candidate_lean_declaration": "target",
        "parent_source_hash": "parent-hash",
        "current_source_hash": stable_hash("theorem target : True"),
        "current_source": "theorem target : True",
        "model_owned_lean_code": True,
        "runtime_selected_lean_code": False,
        "kernel_verified": False,
    }
    stored_feedback = {
        "artifact_kind": "RuntimeFormalizerValidationFailure",
        "failure_id": source_artifact_id,
        "failure_classification": "formalizer_client_tool_loop_exhausted",
        "formalizer_recovery_checkpoint": checkpoint,
        "candidate_materialization_id": "materialization:parent",
    }
    task = AgentTask(
        task_id="formalizer-workspace-continuation:hydrate",
        owner_subsystem="FormalizationEvaluator",
        objective="Continue the exact Lean workspace.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "environment_feedback": {
                "artifact_kind": "RuntimeWorkspaceObservationRef",
                "source_artifact_id": source_artifact_id,
                "source_artifact_hash": stable_hash(stored_feedback),
            },
        },
    )
    blackboard = BlackboardState(
        project_id="hydrate-formalizer-checkpoint",
        artifacts={source_artifact_id: stored_feedback},
    )
    captured: dict[str, object] = {}

    def capture_source_loop(**kwargs):
        captured["environment_feedback"] = kwargs["environment_feedback"]
        captured["task_environment_feedback"] = kwargs["task"].inputs[
            "environment_feedback"
        ]
        raise RuntimeError("stop after hydration observation")

    monkeypatch.setattr(
        runtime_module,
        "_runtime_formalizer_lean_candidate_client_tool_revision",
        capture_source_loop,
    )
    monkeypatch.setattr(
        runtime_module,
        "evaluate_lean_kernel_promotion",
        lambda **kwargs: None,
    )
    subsystem = runtime_module.FormalizerWorkspaceRuntimeSubsystem(
        proposal_agent=object(),
    )

    result = subsystem.run(task, blackboard)

    assert result.failure_classification == "formalizer_provider_generation_failed"
    assert captured["environment_feedback"]["formalizer_recovery_checkpoint"] == (
        checkpoint
    )
    assert captured["task_environment_feedback"] == stored_feedback


def test_formalizer_workspace_rejects_mismatched_observation_ref() -> None:
    question = OpenResearchQuestion(
        id="reject-formalizer-checkpoint",
        title="Reject a mismatched Formalizer checkpoint",
        description="Do not hydrate source state through an invalid artifact ref.",
    )
    source_artifact_id = "formalizer_validation_failure:mismatch"
    stored_feedback = {
        "artifact_kind": "RuntimeFormalizerValidationFailure",
        "failure_id": source_artifact_id,
        "formalizer_recovery_checkpoint": {
            "artifact_kind": "LeanCandidateRevisionRecoveryCheckpoint",
            "current_source": "theorem target : True := by trivial",
        },
    }
    task = AgentTask(
        task_id="formalizer-workspace-continuation:mismatch",
        owner_subsystem="FormalizationEvaluator",
        objective="Continue the exact Lean workspace.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "environment_feedback": {
                "artifact_kind": "RuntimeWorkspaceObservationRef",
                "source_artifact_id": source_artifact_id,
                "source_artifact_hash": "not-the-stored-artifact-hash",
            },
        },
    )
    subsystem = runtime_module.FormalizerWorkspaceRuntimeSubsystem(
        proposal_agent=object(),
    )

    result = subsystem.run(
        task,
        BlackboardState(
            project_id=question.id,
            artifacts={source_artifact_id: stored_feedback},
        ),
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == (
        "formalizer_workspace_observation_ref_invalid"
    )
    assert result.observations[0].payload["source_artifact_present"] is True
    assert result.observations[0].payload["runtime_edits_candidate"] is False


def test_runtime_client_tool_revision_uses_current_hash_bound_workspace(
    tmp_path,
    monkeypatch,
) -> None:
    source = "theorem target : True := by exact True.intro\n"
    artifact_path = tmp_path / "parent.lean"
    artifact_path.write_text(source, encoding="utf-8")
    parent_packet_id = "formalizer_proposal:parent"
    materialization_id = "formalizer_lean_candidate_materialization:parent"
    candidate_id = "target-candidate"
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
            }
        ],
    }
    blackboard = BlackboardState(
        project_id="lean-client-tool-runtime",
        artifacts={
            parent_packet_id: parent_packet,
            materialization_id: materialization,
        },
    )
    task = AgentTask(
        task_id="formalize:q:1234",
        owner_subsystem="FormalizationEvaluator",
        objective="Continue the current Lean workspace.",
    )
    question = OpenResearchQuestion(
        id="q",
        title="Runtime client-tool iteration",
        description="Exercise direct source and Lean feedback iteration.",
    )
    feedback = {
        "source_manifest_id": materialization_id,
        "candidate_diagnostics": [
            {
                "candidate_id": candidate_id,
                "source_hash": stable_hash(source),
                "local_lean_attempted": True,
                "local_lean_compiled": False,
                "local_lean_stderr": "type mismatch",
            }
        ],
        "formalizer_workspace_context": {
            "target_lean_declaration": "target",
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

        def __init__(self, expected_source: str = source) -> None:
            self.expected_source = expected_source
            self.check_result = {}

        def revise_lean_candidate_with_client_tools(self, **kwargs):
            assert kwargs["candidate_id"] == candidate_id
            assert kwargs["initial_source"] == self.expected_source
            assert "reviewed_parent_source_hash" not in kwargs
            self.check_result = dict(
                kwargs["check_candidate"](self.expected_source)
            )
            return (
                {"packet_id": "formalizer_proposal:revised"},
                {
                    "artifact_kind": "LeanCandidateRevisionClientToolLoop",
                    "candidate_id": candidate_id,
                    "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
                    "model_tier": "haiku",
                    "submitted_source_hash": stable_hash(self.expected_source),
                    "runtime_executed_tool_calls": 1,
                    "proof_evidence_status": (
                        "LEAN_CANDIDATE_CLIENT_TOOL_LOOP_RECORDED_NOT_PROOF_EVIDENCE"
                    ),
                },
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
        formal_source_retriever=None,
        proof_search_provider=None,
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=tmp_path,
        lean_candidate_lean_timeout=5,
    )

    assert result is not None
    packet, evidence = result
    assert packet["packet_id"] == "formalizer_proposal:revised"
    assert agent.check_result["compiled"] is True
    assert evidence["parent_candidate_source_hash"] == stable_hash(source)
    assert evidence["resumed_from_model_checkpoint"] is False

    resumed_source = "theorem target : True := by\n  exact True.intro\n"
    resume_feedback = {
        **feedback,
        "formalizer_recovery_checkpoint": {
            "schema_version": 1,
            "artifact_kind": "LeanCandidateRevisionRecoveryCheckpoint",
            "candidate_id": candidate_id,
            "candidate_lean_declaration": "target",
            "parent_source_hash": stable_hash(source),
            "current_source_hash": stable_hash(resumed_source),
            "current_source": resumed_source,
            "transcript_fingerprint": "prior-model-transcript",
            "runtime_selected_lean_code": False,
            "model_owned_lean_code": True,
            "kernel_verified": False,
        },
    }
    resumed = runtime_module._runtime_formalizer_lean_candidate_client_tool_revision(
        proposal_agent=FakeAgent(resumed_source),
        question=question,
        task=task,
        blackboard=blackboard,
        theory_packet={},
        environment_feedback=resume_feedback,
        formal_source_retriever=None,
        proof_search_provider=None,
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=tmp_path,
        lean_candidate_lean_timeout=5,
    )
    assert resumed is not None
    assert resumed[1]["resumed_from_model_checkpoint"] is True
    assert resumed[1]["resume_checkpoint_source_hash"] == stable_hash(
        resumed_source
    )

    stale_feedback = {
        **resume_feedback,
        "formalizer_recovery_checkpoint": {
            **resume_feedback["formalizer_recovery_checkpoint"],
            "current_source_hash": "stale",
        },
    }
    try:
        runtime_module._runtime_formalizer_lean_candidate_client_tool_revision(
            proposal_agent=FakeAgent(resumed_source),
            question=question,
            task=task,
            blackboard=blackboard,
            theory_packet={},
            environment_feedback=stale_feedback,
            formal_source_retriever=None,
            proof_search_provider=None,
            lean_candidate_root=tmp_path / "candidates",
            lean_candidate_local_lean=True,
            lean_candidate_lean_project=tmp_path,
            lean_candidate_lean_timeout=5,
        )
    except PacketValidationError as exc:
        assert exc.validation_label == "Lean workspace checkpoint lineage"
    else:
        raise AssertionError("stale model checkpoint source was not rejected")


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
        "gap_taxonomy": [],
        "critic_findings": [],
        "next_actions": [],
    }
    feedback = {
        "overall_verdict": "ACCEPT",
        "formalizer_workspace_context": {
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
    assert backend.requests[0].metadata["client_tool_loop_max_turns"] == 12

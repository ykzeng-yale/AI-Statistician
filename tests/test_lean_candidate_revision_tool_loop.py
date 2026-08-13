from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.fingerprint import stable_hash
from ai_statistician.agent_runtime import AgentTask, BlackboardState
from ai_statistician.lean_candidate_revision_tool_loop import (
    LEAN_FORMAL_GAP_TOOL,
    LEAN_SOURCE_SUBMISSION_TOOL,
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
    FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP,
    FormalizerConfig,
    LLMFormalizerProofEngineerAgent,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician import (
    lean_candidate_revision_tool_loop as lean_candidate_tool_loop_module,
)
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


def _workspace_snapshot(request: ClientToolTurnRequest) -> dict:
    content = request.messages[0]["content"]
    assert isinstance(content, str)
    encoded = content.split("<CURRENT_WORKSPACE_SNAPSHOT>\n", 1)[1].split(
        "\n</CURRENT_WORKSPACE_SNAPSHOT>", 1
    )[0]
    return json.loads(encoded)


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
                    "submit-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": repaired},
                )
            ),
        ]
    )
    checked_sources: list[str] = []
    searches: list[tuple[str, int]] = []

    def check(source: str, _declaration: str):
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
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=search,
    )

    assert result.lean_source == repaired
    assert result.source_hash == stable_hash(repaired)
    assert checked_sources == [initial, repaired]
    assert searches == [("True.intro declaration", 3)]
    assert result.evidence["runtime_selected_lean_code"] is False
    assert result.evidence["model_owned_lean_code"] is True
    assert result.evidence["runtime_executed_tool_calls"] == 2
    assert result.evidence["local_lean_checks"] == 2
    assert result.evidence["formal_environment_searches"] == 1
    assert result.evidence["model"] == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    assert all(
        request.model == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
        for request in backend.requests
    )
    assert set(tool.name for tool in backend.requests[0].tools) == {
        LEAN_SOURCE_SUBMISSION_TOOL,
        "search_formal_environment",
    }
    assert all(request.disable_parallel_tool_use for request in backend.requests)
    initial_snapshot = _workspace_snapshot(backend.requests[0])
    assert initial_snapshot["current_lean_source"] == initial
    assert initial_snapshot["latest_check_observation"][
        "local_lean_stderr"
    ] == "unknown module"
    assert result.evidence["handoff_mode"] == (
        "successful_model_source_submission"
    )
    assert result.evidence["model_explicit_submit"] is True
    assert result.evidence["submit_and_check_atomic"] is True


def test_lean_candidate_tool_loop_authors_first_source_from_empty_workspace() -> None:
    authored = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-initial-source",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": authored,
                        "candidate_declaration_name": "target",
                    },
                )
            )
        ]
    )
    checked_sources: list[str] = []
    checked_declarations: list[str] = []

    def check(source: str, declaration: str):
        checked_sources.append(source)
        checked_declarations.append(declaration)
        return {
            "source_hash": stable_hash(source),
            "compiled": source == authored,
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Author the bound target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="",
        initial_source="",
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
    )

    assert checked_sources == [authored]
    assert checked_declarations == ["target"]
    assert result.lean_source == authored
    assert result.candidate_lean_declaration == "target"
    assert result.evidence["workspace_phase"] == "initial_authoring"
    assert result.evidence["parent_source_hash"] == stable_hash("")
    assert result.evidence["source_updates"] == 1
    assert result.evidence["artifact_kind"] == (
        "LeanCandidateClientToolWorkspace"
    )
    assert result.evidence["runtime_selected_lean_code"] is False
    submit_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == LEAN_SOURCE_SUBMISSION_TOOL
    )
    assert submit_tool.input_schema["required"] == [
        "lean_source",
        "candidate_declaration_name",
    ]


def test_formal_gap_tool_keeps_model_authored_errors_in_source_revision_loop() -> None:
    tools = lean_candidate_tool_loop_module._lean_candidate_revision_tools(
        include_formal_gap=True,
    )
    gap_tool = next(tool for tool in tools if tool.name == LEAN_FORMAL_GAP_TOOL)

    assert "current model-authored source" in gap_tool.description
    assert "rewrite the complete source" in gap_tool.description
    assert "corresponding tool observation" in gap_tool.description


def test_lean_candidate_workspace_lets_model_report_task_bound_formal_gap() -> None:
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "report-gap",
                    LEAN_FORMAL_GAP_TOOL,
                    {
                        "summary": "The active project lacks the required primitive.",
                        "missing_primitives": ["Required.Primitive"],
                    },
                )
            )
        ]
    )

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Formalize the bound target or report concrete blockers.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="",
        initial_source="",
        check_candidate=lambda source, declaration: {},
        search_formal_environment=lambda query, k: [],
        allow_formal_gap=True,
    )

    assert result.disposition == "FORMAL_GAP"
    assert result.lean_source == ""
    assert result.formal_gap["missing_primitives"] == ["Required.Primitive"]
    assert result.evidence["model_owned_lean_code"] is False
    assert result.evidence["runtime_selected_lean_code"] is False
    assert result.evidence["kernel_verified"] is False


def test_formal_gap_preserves_prior_model_source_and_exact_lean_observation() -> None:
    attempted = "theorem target : True := by\n  sorry\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-attempt",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": attempted,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "report-gap",
                    LEAN_FORMAL_GAP_TOOL,
                    {
                        "summary": "The exact target needs a missing project lemma.",
                        "missing_primitives": ["Project.requiredLemma"],
                        "blocking_observations": [
                            "The submitted source retains sorryAx."
                        ],
                    },
                )
            ),
        ]
    )

    def check(source: str, declaration: str):
        assert source == attempted
        assert declaration == "target"
        return {
            "source_hash": stable_hash(source),
            "compiled": False,
            "local_lean_source_compiled": True,
            "candidate_identity_lean_verified": False,
            "local_lean_stderr": "target depends on axioms: [sorryAx]",
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Formalize the exact target or report a concrete gap.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="",
        initial_source="",
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        allow_formal_gap=True,
    )

    assert result.disposition == "FORMAL_GAP"
    assert result.lean_source == attempted
    assert result.candidate_lean_declaration == "target"
    assert result.check_result["local_lean_stderr"].endswith("[sorryAx]")
    assert result.evidence["model_explicit_submit"] is True
    assert result.evidence["model_owned_lean_code"] is True
    assert result.evidence["latest_check_compiled"] is True
    assert result.evidence["local_candidate_validation_passed"] is False
    assert result.evidence["independent_semantic_review_required"] is False
    assert result.evidence["kernel_verified"] is False


def test_formalizer_agent_keeps_formal_gap_available_after_workspace_resume() -> None:
    source = "theorem target : True := by\n  sorry\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "report-resumed-gap",
                    LEAN_FORMAL_GAP_TOOL,
                    {
                        "summary": "The checked target needs a missing project lemma.",
                        "missing_primitives": ["Project.requiredLemma"],
                        "blocking_observations": [
                            "The active source remains dependent on sorryAx."
                        ],
                    },
                )
            )
        ]
    )
    agent = LLMFormalizerProofEngineerAgent(
        provider=backend,
        config=FormalizerConfig(
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            max_tokens=1200,
            client_tool_lean_candidate_max_turns=2,
        ),
    )

    packet, evidence = agent.run_lean_candidate_workspace_with_client_tools(
        question=OpenResearchQuestion(
            id="resumed-gap",
            title="Resume an exact target",
            description="Continue the same target or report a concrete gap.",
        ),
        theory_packet={"packet_id": "theory:resumed-gap"},
        parent_packet={
            "artifact_kind": "FormalizerProofEngineerProposalPacket",
            "packet_id": "formalizer:resumed-gap",
            "formal_targets": [
                {
                    "id": "target-candidate",
                    "formal_target_role": "SOURCE_THEOREM_CANDIDATE",
                    "candidate_lean_declaration": "target",
                    "informal_source": "The exact target.",
                    "lean_statement_sketch": source,
                    "lean_imports": [],
                    "expected_status": "NEEDS_KERNEL_CHECK",
                    "source_theorem_target_provenance": {
                        "source_theorem_target_known": True,
                        "source_theorem_goal_id": "goal-target",
                        "target_lean_declaration": "target",
                    },
                }
            ],
            "retrieval_queries": [],
            "gap_taxonomy": [],
        },
        candidate_id="target-candidate",
        candidate_source_field="formal_targets",
        candidate_lean_declaration="target",
        initial_source=source,
        environment_feedback={},
        check_candidate=lambda current, _declaration: {
            "source_hash": stable_hash(current),
            "compiled": False,
            "local_lean_stderr": "target depends on axioms: [sorryAx]",
        },
        search_formal_environment=lambda query, k: [],
    )

    assert LEAN_FORMAL_GAP_TOOL in {
        tool.name for tool in backend.requests[0].tools
    }
    assert "your own submitted source is revision feedback" in (
        backend.requests[0].system_prompt
    )
    assert "inspected declaration source" in backend.requests[0].system_prompt
    assert "prioritize a complete source revision" in (
        backend.requests[0].system_prompt
    )
    assert evidence["disposition"] == "FORMAL_GAP"
    assert evidence["local_lean_checks"] == 1
    assert evidence["model_explicit_submit"] is False
    assert evidence["model_owned_lean_code"] is True
    assert evidence["kernel_verified"] is False
    target = packet["formal_targets"][0]
    assert target["formal_target_role"] == (
        FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP
    )
    assert target["lean_statement_sketch"] == ""
    assert target["candidate_lean_declaration"] == ""
    assert target["formal_gap"]["missing_primitives"] == [
        "Project.requiredLemma"
    ]


def test_search_observation_reuses_retained_source_and_raw_lean_feedback() -> None:
    failing = "theorem target : True := by\n  exact missing\n"
    passing = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-failing",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": failing},
                )
            ),
            _response(
                ClientToolCall(
                    "search-after-failure",
                    "search_formal_environment",
                    {"query": "missing declaration"},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-passing",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": passing},
                )
            ),
        ]
    )

    def check(source: str, _declaration: str):
        return {
            "source_hash": stable_hash(source),
            "compiled": source == passing,
            "local_lean_stdout": (
                "unknown identifier 'missing'" if source == failing else ""
            ),
        }

    run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Author the exact target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source="",
        check_candidate=check,
        search_formal_environment=lambda query, k: {"query": query, "hits": []},
    )

    search_result = json.loads(
        backend.requests[2].messages[-1]["content"][0]["content"]
    )
    assert search_result["current_source_hash"] == stable_hash(failing)
    assert "current_lean_source" not in search_result
    assert "latest_lean_check" not in search_result
    retained_check = json.loads(
        backend.requests[2].messages[-3]["content"][0]["content"]
    )
    assert retained_check["local_lean_stdout"] == (
        "unknown identifier 'missing'"
    )


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
                    "submit-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": model_source},
                )
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

    def check(source: str, _declaration: str):
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
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        search_proof_candidates=search,
    )

    assert proof_search_calls == [
        (
            initial,
            "close target from current goal",
            2,
            {"source_hash": stable_hash(initial), "compiled": False},
        )
    ]
    assert checked_sources == [initial, model_source]
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
            _response(
                ClientToolCall(
                    "submit-initial",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": initial},
                )
            ),
            _response(ClientToolCall("state-1", "inspect_lean_state", {})),
            _response(
                ClientToolCall(
                    "submit-revised",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": revised},
                )
            ),
        ]
    )
    inspections: list[tuple[str, dict]] = []

    def check(source: str, _declaration: str):
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
    assert all(
        "inspect_lean_state" in {tool.name for tool in request.tools}
        for request in backend.requests
    )


def test_model_selects_exact_declaration_inspection_inside_same_source_loop() -> None:
    initial = (
        "import Project.Library\n"
        "#check Example.Source\n"
        "theorem target : True := by\n  exact missing\n"
    )
    revised = (
        "import Project.Library\n"
        "#check Example.Source\n"
        "theorem target : True := by\n  exact True.intro\n"
    )
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-initial",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": initial},
                )
            ),
            _response(
                ClientToolCall(
                    "declaration-1",
                    "inspect_lean_declaration",
                    {"symbol": "Example.Source", "context_lines": 80},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-revised",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": revised},
                )
            ),
        ]
    )
    inspections: list[tuple[str, str, int, dict]] = []

    def check(source: str, _declaration: str):
        return {
            "source_hash": stable_hash(source),
            "compiled": source == revised,
            "artifact_path": "/project/Candidate.lean",
            "local_lean_stderr": "unknown identifier 'missing'"
            if source == initial
            else "",
        }

    def inspect(source: str, symbol: str, context_lines: int, last_check):
        inspections.append(
            (source, symbol, context_lines, dict(last_check))
        )
        return {
            "ok": True,
            "status": "OBSERVED",
            "executed_tools": [
                "lean_lsp_mcp.lean_declaration_file"
            ],
            "observation": {
                "content": "structure Source where\n  field : Nat\n"
            },
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Inspect declarations and revise the exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        inspect_lean_declaration=inspect,
    )

    assert inspections[0][:3] == (
        initial,
        "Example.Source",
        40,
    )
    assert inspections[0][3]["source_hash"] == stable_hash(initial)
    assert result.lean_source == revised
    assert result.evidence["lean_declaration_inspections"] == 1
    assert result.evidence["lean_declaration_provider_tools"] == [
        "lean_lsp_mcp.lean_declaration_file"
    ]
    assert result.evidence["lean_lsp_mcp_live_called"] is True
    assert "inspect_lean_declaration" in {
        tool.name for tool in backend.requests[0].tools
    }
    assert "inspect_lean_declaration" in {
        tool.name for tool in backend.requests[1].tools
    }


def test_model_can_inspect_exact_declaration_before_first_source() -> None:
    authored = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "declaration-before-source",
                    "inspect_lean_declaration",
                    {"symbol": "True.intro", "context_lines": 12},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-first-source",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": authored,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    inspections: list[tuple[str, str, int, dict]] = []

    def inspect(source: str, symbol: str, context_lines: int, last_check):
        inspections.append((source, symbol, context_lines, dict(last_check)))
        return {
            "ok": True,
            "status": "OBSERVED",
            "executed_tools": ["lean_lsp_mcp.lean_declaration_file"],
            "observation": {"content": "theorem True.intro : True"},
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Inspect the active API, then author the exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="",
        initial_source="",
        check_candidate=lambda source, declaration: {
            "source_hash": stable_hash(source),
            "compiled": source == authored and declaration == "target",
        },
        search_formal_environment=lambda query, k: [],
        inspect_lean_declaration=inspect,
    )

    assert inspections == [("", "True.intro", 12, {})]
    assert result.lean_source == authored
    assert result.evidence["lean_declaration_inspections"] == 1
    assert result.evidence["lean_lsp_mcp_live_called"] is True
    assert "inspect_lean_declaration" in {
        tool.name for tool in backend.requests[0].tools
    }


def test_lean_candidate_tool_loop_keeps_core_actions_available_across_turns() -> None:
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
                    "submit-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": revised},
                )
            ),
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
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=lambda source, _declaration: {
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
        LEAN_SOURCE_SUBMISSION_TOOL,
        "search_formal_environment",
    ]
    assert backend.requests[1].tool_choice == "any"
    assert all(request.disable_parallel_tool_use for request in backend.requests)


def test_lean_candidate_workspace_keeps_stable_tools_and_current_snapshot() -> None:
    authored = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            *[
                _response(
                    ClientToolCall(
                        f"search-{index}",
                        "search_formal_environment",
                        {"query": f"declaration query {index}"},
                    )
                )
                for index in range(5)
            ],
            _response(
                ClientToolCall(
                    "submit-source",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": authored},
                )
            ),
        ]
    )

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Retain observations and author the exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=7,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source="",
        check_candidate=lambda source, _declaration: {
            "source_hash": stable_hash(source),
            "compiled": source == authored,
        },
        search_formal_environment=lambda query, k: {
            "query": query,
            "max_results": k,
        },
    )

    expected_tools = {
        LEAN_SOURCE_SUBMISSION_TOOL,
        "search_formal_environment",
    }
    assert all(
        {tool.name for tool in request.tools} == expected_tools
        for request in backend.requests
    )
    assert len(backend.requests[-1].messages) == 9
    final_context = json.dumps(backend.requests[-1].messages, sort_keys=True)
    assert "declaration query 0" not in final_context
    assert all(
        f"declaration query {index}" in final_context for index in range(1, 5)
    )
    assert final_context.count("CURRENT_WORKSPACE_SNAPSHOT") == 2
    snapshot = _workspace_snapshot(backend.requests[-1])
    assert snapshot["budget"]["standard_turns_remaining_including_current"] == 2
    assert "latest_formal_environment_search" not in snapshot
    assert "latest_proof_search" not in snapshot
    assert "latest_state_inspection" not in snapshot
    assert "latest_declaration_inspection" not in snapshot
    assert result.evidence["max_retained_tool_turns"] == 4
    assert result.evidence["max_terminal_recovery_turns"] == 1
    assert result.evidence["transcript_policy"] == (
        "rolling_history_plus_authoritative_snapshot"
    )
    assert result.evidence["tool_surface_policy"] == "stable_for_workspace"
    assert result.evidence["formal_environment_searches"] == 5
    assert "max_consecutive_context_actions" not in result.evidence
    assert "context_actions_since_source_submission" not in result.evidence


def test_lean_candidate_workspace_reads_final_compile_error_in_recovery_turn() -> None:
    initial = "theorem target : True := by\n  sorry\n"
    failing = "theorem target : True := by\n  exact missing_name\n"
    compiled = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-failing",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": failing},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-compiled",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": compiled},
                )
            ),
        ]
    )

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise the complete source from raw Lean observations.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=1,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=lambda source, _declaration: {
            "source_hash": stable_hash(source),
            "compiled": source == compiled,
            "local_lean_stderr": (
                "unknown identifier 'missing_name'" if source == failing else ""
            ),
        },
        search_formal_environment=lambda query, k: [],
    )

    assert result.lean_source == compiled
    assert result.evidence["turns"] == 2
    assert result.evidence["max_turns"] == 1
    assert result.evidence["max_terminal_recovery_turns"] == 1
    assert [tool.name for tool in backend.requests[1].tools] == [
        LEAN_SOURCE_SUBMISSION_TOOL
    ]
    assert backend.requests[1].tool_choice == LEAN_SOURCE_SUBMISSION_TOOL
    recovery_snapshot = _workspace_snapshot(backend.requests[1])
    assert recovery_snapshot["current_lean_source"] == failing
    assert recovery_snapshot["latest_check_observation"][
        "local_lean_stderr"
    ] == "unknown identifier 'missing_name'"
    assert recovery_snapshot["budget"]["terminal_recovery_turn"] is True


def test_lean_candidate_workspace_revises_after_context_stall_compile_error() -> None:
    failing = "theorem target : True := by\n  exact missing_name\n"
    compiled = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "search-1",
                    "search_formal_environment",
                    {"query": "target premise"},
                )
            ),
            _response(
                ClientToolCall(
                    "search-2",
                    "search_formal_environment",
                    {"query": "target premise"},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-failing",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": failing},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-compiled",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": compiled},
                )
            ),
        ]
    )

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Author the exact target or report a grounded gap.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=5,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source="",
        check_candidate=lambda source, _declaration: {
            "source_hash": stable_hash(source),
            "compiled": source == compiled,
            "local_lean_stderr": (
                "unknown identifier 'missing_name'" if source == failing else ""
            ),
        },
        search_formal_environment=lambda query, k: {
            "query": query,
            "max_results": k,
            "results": [],
        },
        allow_formal_gap=True,
    )

    assert result.lean_source == compiled
    assert result.evidence["turns"] == 4
    assert result.evidence["source_updates"] == 2
    assert result.evidence["local_lean_checks"] == 2
    assert all(
        [tool.name for tool in request.tools]
        == [LEAN_SOURCE_SUBMISSION_TOOL, LEAN_FORMAL_GAP_TOOL]
        for request in backend.requests[-2:]
    )
    recovery_snapshot = _workspace_snapshot(backend.requests[-1])
    assert recovery_snapshot["budget"][
        "terminal_recovery_turn"
    ] is True
    assert recovery_snapshot["current_lean_source"] == failing
    assert recovery_snapshot["latest_check_observation"][
        "local_lean_stderr"
    ] == "unknown identifier 'missing_name'"
    assert backend.requests[-1].metadata[
        "client_tool_loop_terminal_decision_reason"
    ] == "repeated client-tool turns made no new progress"


def test_global_budget_does_not_revoke_lean_edit_after_multiple_failures() -> None:
    sources = [
        f"theorem target : True := by\n  exact candidate_{index}\n"
        for index in range(4)
    ]
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    f"submit-{index}",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": source},
                )
            )
            for index, source in enumerate(sources)
        ]
    )

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Keep revising from each exact compiler observation.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source="theorem target : True := by\n  sorry\n",
        check_candidate=lambda source, _declaration: {
            "source_hash": stable_hash(source),
            "compiled": source == sources[-1],
            "local_lean_stderr": "unknown identifier"
            if source != sources[-1]
            else "",
        },
        search_formal_environment=lambda query, k: [],
    )

    assert result.lean_source == sources[-1]
    assert result.evidence["source_updates"] == 4
    assert result.evidence["local_lean_checks"] == 5
    assert all(
        LEAN_SOURCE_SUBMISSION_TOOL in {tool.name for tool in request.tools}
        for request in backend.requests
    )


def test_lean_candidate_tool_loop_hands_off_on_successful_requested_check() -> None:
    initial = "theorem target : True := by trivial\n"
    revised = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": revised},
                )
            ),
        ]
    )

    def check(source: str, _declaration: str):
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
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
    )

    assert result.lean_source == revised
    assert len(backend.requests) == 1
    assert result.evidence["local_lean_checks"] == 2
    assert result.evidence["handoff_mode"] == (
        "successful_model_source_submission"
    )


def test_lean_candidate_tool_loop_stops_repeated_identical_submissions() -> None:
    source = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": source},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-2",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": source},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-3",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": source},
                )
            ),
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
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=source,
            check_candidate=lambda current, _declaration: {
                "source_hash": stable_hash(current),
                "compiled": False,
                "local_lean_stderr": "same compiler diagnostic",
            },
            search_formal_environment=lambda query, k: [],
        )
    except PacketValidationError as exc:
        assert "no new progress" in " ".join(exc.errors)
        assert exc.recovery_checkpoint["checks"] == 1
    else:
        raise AssertionError("repeated identical Lean submissions did not stop")


def test_lean_candidate_tool_loop_checks_final_submission_at_turn_budget() -> None:
    initial = "theorem target : True := by exact True.intro\n"
    repaired = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-final",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": repaired},
                )
            ),
        ]
    )
    checked_sources: list[str] = []

    def check(source: str, _declaration: str):
        checked_sources.append(source)
        return {
            "source_hash": stable_hash(source),
            "compiled": source == repaired,
            "local_lean_stderr": "" if source == repaired else "initial failure",
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise this target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=1,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
    )

    assert result.lean_source == repaired
    assert checked_sources == [initial, repaired]


def test_lean_candidate_tool_loop_preserves_uncompiled_latest_edit_checkpoint() -> None:
    initial = "theorem target : True := by exact True.intro\n"
    latest = "theorem target : False := by exact False.elim (by contradiction)\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-final",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": latest},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-identical-recovery",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": latest},
                )
            ),
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
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=initial,
            check_candidate=lambda source, _declaration: {
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
            "LeanCandidateWorkspaceRecoveryCheckpoint"
        )
        assert checkpoint["current_source"] == latest
        assert checkpoint["current_source_hash"] == stable_hash(latest)
        assert checkpoint["last_check"]["source_hash"] == stable_hash(latest)
        assert checkpoint["latest_check_observation"]["source_hash"] == (
            stable_hash(latest)
        )
        assert checkpoint["parent_source_hash"] == stable_hash(initial)
        assert checkpoint["max_terminal_recovery_turns"] == 1
        assert "final_runtime_check_performed" not in checkpoint
        assert checkpoint["model_owned_lean_code"] is True
        assert checkpoint["kernel_verified"] is False
    else:
        raise AssertionError("uncompiled final source was not checkpointed")


def test_lean_candidate_prompt_leaves_current_workspace_state_to_snapshot() -> None:
    exact_error = (
        "type mismatch\n"
        + "x" * 4000
        + "EXACT_MIDDLE_LEAN_OBSERVATION"
        + "y" * 4000
    )
    initial_source = "theorem target : True := by\n  exact True.intro\n"
    prompt = formalizer_module._build_lean_candidate_workspace_tool_prompt(
        question=OpenResearchQuestion(
            id="compact-context",
            title="Compact Lean context",
            description="Keep exact target context and retrieve signatures on demand.",
        ),
        theory_packet={
            "packet_id": "theory:compact",
            "theorem_cards": [
                {
                    "id": "theory-target",
                    "conclusion": "EXACT_PARENT_THEORY_CONCLUSION",
                }
            ],
        },
        parent_packet={
            "packet_id": "formalizer_proposal:compact",
            "formal_targets": [
                {
                    "id": "target-candidate",
                    "formal_target_role": "SOURCE_THEOREM_CANDIDATE",
                    "informal_source": "The exact target remains true.",
                    "candidate_lean_declaration": "target",
                    "semantic_alignment_constraints": [
                        "Preserve the exact non-vacuous target."
                    ],
                    "source_theorem_target_provenance": {
                        "source_theorem_goal_id": "goal-1",
                        "source_theorem_target_known": True,
                        "target_lean_declaration": "target",
                    },
                    "expected_status": "NEEDS_KERNEL_CHECK",
                }
            ],
        },
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
                "formal_source_grounding_hits": [
                    {
                        "query_role": "target_api",
                        "hits": [
                            {
                                "source_id": "statlib",
                                "name": "Statlib.Target.exact_support",
                                "signature": (
                                    "theorem Statlib.Target.exact_support : True"
                                ),
                                "declaration_source_context": {
                                    "module": "Statlib.Target"
                                },
                                "source_activation": {
                                    "relation_to_active_project": (
                                        "direct_lake_dependency"
                                    ),
                                    "classification": (
                                        "active_project_import_closure_candidate"
                                    ),
                                },
                            }
                        ],
                    }
                ],
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
    assert "current_lean_source" not in payload
    assert payload["task_bound_theory_context"]["theorem_cards"][0][
        "conclusion"
    ] == "EXACT_PARENT_THEORY_CONCLUSION"
    assert payload["exact_target_contract"] == {
        "id": "target-candidate",
        "formal_target_role": "SOURCE_THEOREM_CANDIDATE",
        "informal_source": "The exact target remains true.",
        "candidate_lean_declaration": "target",
        "semantic_alignment_constraints": [
            "Preserve the exact non-vacuous target."
        ],
        "source_theorem_target_provenance": {
            "source_theorem_goal_id": "goal-1",
            "source_theorem_target_known": True,
            "target_lean_declaration": "target",
        },
        "expected_status": "NEEDS_KERNEL_CHECK",
    }
    feedback = payload["runtime_observations"]
    context = feedback["target_and_environment_observations"]
    assert context["target_theorem_statement"] == "theorem target : True"
    assert "proof_state_trace_rag" not in context
    assert "formal_source_grounding_hits" not in context
    assert payload["indexed_lean_environment_candidates"] == [
        {
            "source_id": "statlib",
            "module": "Statlib.Target",
            "qualified_declaration": "Statlib.Target.exact_support",
            "query_role": "target_api",
            "relation_to_active_project": "direct_lake_dependency",
            "candidate_classification": (
                "active_project_import_closure_candidate"
            ),
            "import_readiness": "direct_dependency_indexed_module",
            "signature": "theorem Statlib.Target.exact_support : True",
        }
    ]
    assert "do not repeat a search for the same identity" in payload[
        "tool_workflow"
    ]
    assert "candidate_rerun_specs" not in context
    assert "reviewed_source_artifacts" not in feedback
    observation = feedback["candidate_diagnostics"][0]
    assert "lean_source_excerpt" not in observation
    assert observation["local_lean_stderr"] == exact_error
    checkpoint = feedback["model_revision_checkpoint"]
    assert checkpoint["current_source_hash"] == stable_hash(initial_source)
    assert "current_source" not in checkpoint
    assert "last_check" not in checkpoint
    assert "latest_check_observation" not in checkpoint
    assert "latest_state_inspection" not in checkpoint
    assert "EXACT_MIDDLE_LEAN_OBSERVATION" in prompt
    assert "formalizer_workspace_context" not in feedback
    assert "required_repair" not in prompt
    assert "recommended_repair" not in prompt
    assert len(prompt) < 20000


def test_formalizer_workspace_target_reuses_upstream_goal_without_model_call() -> None:
    question = OpenResearchQuestion(
        id="workspace-target",
        title="Bind an exact theorem",
        description="Reuse upstream identity before direct Lean authoring.",
    )
    target = formalizer_module.build_formalizer_workspace_target(
        question=question,
        theory_packet={
            "theory_derivation_packet": {
                "formalization_handoff": {
                    "source_theorem_target": "goal-1",
                    "semantic_alignment_constraints": [
                        "Preserve every assumption."
                    ],
                }
            }
        },
        registered_problem={},
        theorem_goals=[
            {
                "id": "goal-1",
                "title": "Exact goal",
                "informal_statement": "The exact unchanged theorem target.",
            },
            {
                "id": "goal-2",
                "title": "Deferred goal",
                "informal_statement": "A different theorem.",
            },
        ],
    )

    assert target["artifact_kind"] == "FormalizerWorkspaceTarget"
    assert target["formal_target"]["id"] == "goal-1"
    assert target["formal_target"]["informal_source"] == (
        "The exact unchanged theorem target."
    )
    assert target["formal_target"]["semantic_alignment_constraints"] == [
        "Preserve every assumption."
    ]
    assert target["formal_target"]["lean_statement_sketch"] == ""
    assert target["formal_target"]["candidate_lean_declaration"] == ""
    assert target["proof_evidence_status"] == (
        "TASK_BOUND_TARGET_REFERENCE_NOT_PROOF_EVIDENCE"
    )


def test_exhausted_formalizer_source_loop_blocks_without_duplicate_workspace() -> None:
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

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == "formalizer_client_tool_loop_exhausted"
    failure = next(iter(result.produced_artifacts.values()))
    assert failure["formalizer_recovery_checkpoint"]["current_source"] == latest
    assert failure["rejected_candidate_complete"] is False
    assert failure["complete_current_source_checkpoint_provided"] is True
    assert failure["validation_boundary"][
        "complete_rejected_candidate_provided"
    ] is False
    assert failure["validation_boundary"][
        "complete_current_source_checkpoint_provided"
    ] is True
    assert failure["model_generation_attempts"] == 2
    assert failure["client_tool_turns"] == 0
    assert "workspace_continuation_allowed" not in failure
    assert "internal_json_regeneration_attempts" not in failure
    assert "without launching a packet-regeneration session" in result.rationale
    assert failure["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")


def test_formalizer_failure_preserves_workspace_refs_without_payload_copy() -> None:
    source = "theorem target : True := by\n  exact True.intro\n"
    source_hash = stable_hash(source)
    packet_id = "formalizer_proposal:parent"
    materialization_id = "formalizer_lean_candidate_materialization:parent"
    parent_packet = {
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": packet_id,
        "formal_targets": [
            {
                "id": "target-candidate",
                "candidate_lean_declaration": "target",
                "informal_source": "Exact target",
            }
        ],
    }
    materialization = {
        "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
        "manifest_id": materialization_id,
        "source_formalizer_packet_id": packet_id,
        "candidate_rows": [],
    }
    checkpoint = {
        "artifact_kind": "LeanCandidateRevisionRecoveryCheckpoint",
        "candidate_id": "target-candidate",
        "candidate_lean_declaration": "target",
        "parent_source_hash": stable_hash("older source"),
        "current_source_hash": source_hash,
        "current_source": source,
        "source_updates": 1,
        "checks": 1,
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "last_check": {
            "source_hash": source_hash,
            "compiled": False,
            "local_lean_stdout": "raw Lean diagnostic",
        },
        "model_owned_lean_code": True,
        "runtime_selected_lean_code": False,
        "kernel_verified": False,
    }
    result = runtime_module._formalizer_packet_validation_failure_result(
        task=AgentTask(
            task_id="formalize:preserve-workspace",
            owner_subsystem="FormalizationEvaluator",
            objective="Continue the exact source workspace.",
            inputs={"environment_feedback": {}},
        ),
        question=OpenResearchQuestion(
            id="preserve-workspace",
            title="Preserve workspace",
            description="Retain refs and the current model source.",
        ),
        theory_packet_id="theory:parent",
        simulation_manifest_id="",
        algorithm_sandbox_manifest_id="",
        exc=PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool revision",
            attempts=4,
            errors=["global client-tool turn budget exhausted"],
            history=[
                {
                    "turn_index": 0,
                    "result_excerpt": "raw transcript observation" * 10000,
                    "tool_calls": [
                        {"name": "search_formal_environment"},
                        {"name": LEAN_SOURCE_SUBMISSION_TOOL},
                    ],
                }
            ],
            recovery_checkpoint=checkpoint,
        ),
        environment_feedback={
            "source_manifest_id": materialization_id,
            "source_formalizer_packet_id": packet_id,
            "candidate_id": "target-candidate",
            "formalizer_workspace_context": {
                "candidate_id": "target-candidate",
                "target_lean_declaration": "target",
                "semantic_alignment_constraints": ["Preserve the exact target"],
                "formal_source_scope_ids": ["active-project"],
                "formal_source_grounding_hits": [
                    {"hits": ["redundant retrieval payload" * 10000]}
                ],
            },
            "prior_environment_feedback": {
                "recursive": "nested history" * 10000
            },
        },
        workspace_artifacts={
            packet_id: parent_packet,
            materialization_id: materialization,
        },
    )

    failure_ids = [
        artifact_id
        for artifact_id in result.produced_artifacts
        if artifact_id.startswith("formalizer_validation_failure:")
    ]
    attempt_history_ids = [
        artifact_id
        for artifact_id in result.produced_artifacts
        if artifact_id.startswith("formalizer_attempt_history:")
    ]
    assert len(failure_ids) == 1
    assert len(attempt_history_ids) == 1
    assert set(result.produced_artifacts) == {
        packet_id,
        materialization_id,
        attempt_history_ids[0],
        failure_ids[0],
    }
    failure = next(
        artifact
        for artifact_id, artifact in result.produced_artifacts.items()
        if artifact_id.startswith("formalizer_validation_failure:")
    )
    assert failure["source_manifest_id"] == materialization_id
    assert failure["source_formalizer_packet_id"] == packet_id
    assert failure["formalizer_recovery_checkpoint"]["current_source"] == source
    assert "formal_source_grounding_hits" not in failure[
        "formalizer_workspace_context"
    ]
    assert "prior_environment_feedback" not in failure
    assert "prior_environment_observations" not in failure
    assert len(json.dumps(failure)) < 20000
    assert failure["attempt_history_ref"]["artifact_id"] == (
        attempt_history_ids[0]
    )
    attempt_history = result.produced_artifacts[attempt_history_ids[0]]
    assert attempt_history["attempts"][0]["result_excerpt"].startswith(
        "raw transcript observation"
    )
    assert "result_excerpt" not in json.dumps(failure)
    assert failure["model_generation_attempts"] == 4
    assert failure["client_tool_turns"] == 1
    loop_evidence = result.evidence_entries[0].payload
    assert loop_evidence["model_owned_lean_code"] is True
    assert loop_evidence["runtime_selected_lean_code"] is False
    assert loop_evidence["source_changed"] is True
    assert loop_evidence["source_updates"] == 1
    assert loop_evidence["local_lean_checks"] == 1
    assert loop_evidence["latest_check_compiled"] is False
    assert loop_evidence["n_formal_rag_tool_calls"] == 1


def test_formalizer_packet_failure_blocks_without_regeneration_session() -> None:
    question = OpenResearchQuestion(
        id="packet-owner-loop",
        title="Keep packet failure with its source owner",
        description="Routine source validation must not invoke Architect routing.",
    )
    task = AgentTask(
        task_id="formalize:packet-owner-loop",
        owner_subsystem="FormalizationEvaluator",
        objective="Author the complete exact-target Lean packet.",
        inputs={"environment_feedback": {}},
    )
    error = PacketValidationError(
        validation_label="LLM Formalizer packet",
        attempts=2,
        errors=[
            "capability_eval requires at least one model-authored complete Lean "
            "source in formal_targets"
        ],
        history=[],
    )

    result = runtime_module._formalizer_packet_validation_failure_result(
        task=task,
        question=question,
        theory_packet_id="theory:packet-owner-loop",
        simulation_manifest_id="",
        algorithm_sandbox_manifest_id="",
        exc=error,
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    assert result.failure_classification == "formalizer_packet_validation_failed"
    failure = next(iter(result.produced_artifacts.values()))
    assert failure["model_generation_attempts"] == 2
    assert failure["client_tool_turns"] == 0
    assert "workspace_continuation_allowed" not in failure
    assert (
        "without launching another generation session" in result.rationale
    )


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
        "_runtime_formalizer_lean_candidate_client_tool_workspace",
        capture_source_loop,
    )
    monkeypatch.setattr(
        runtime_module,
        "_runtime_formalizer_client_tool_workspace_available",
        lambda **kwargs: True,
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
        use_client_tool_lean_candidate_workspace = True

    class FakeProvider:
        def generate_client_tool_turn(self, request):
            raise AssertionError("fake agent owns the isolated method call")

    class FakeAgent:
        config = FakeConfig()
        provider = FakeProvider()

        def __init__(
            self,
            expected_source: str = source,
            inspection_symbol: str = "Example.Source",
        ) -> None:
            self.expected_source = expected_source
            self.inspection_symbol = inspection_symbol
            self.check_result = {}
            self.declaration_result = {}

        def run_lean_candidate_workspace_with_client_tools(self, **kwargs):
            assert kwargs["candidate_id"] == candidate_id
            assert kwargs["initial_source"] == self.expected_source
            assert "reviewed_parent_source_hash" not in kwargs
            self.check_result = dict(
                    kwargs["check_candidate"](self.expected_source, "target")
            )
            declaration_tool = kwargs.get("inspect_lean_declaration")
            assert callable(declaration_tool)
            self.declaration_result = dict(
                declaration_tool(
                    self.expected_source,
                    self.inspection_symbol,
                    10,
                    self.check_result,
                )
            )
            return (
                {"packet_id": "formalizer_proposal:revised"},
                {
                    "artifact_kind": "LeanCandidateClientToolWorkspace",
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

    class FakeProofStateProvider:
        name = "fake_lean_lsp_mcp"

        def __init__(self) -> None:
            self.calls: list[dict] = []

        def inspect_declaration(self, **kwargs):
            self.calls.append(dict(kwargs))
            return {
                "ok": True,
                "status": "OBSERVED",
                "symbol": kwargs["symbol"],
                "observation": {"content": "structure Source where"},
                "proof_evidence_status": (
                    "LEAN_DECLARATION_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }

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
    proof_state_provider = FakeProofStateProvider()
    result = runtime_module._runtime_formalizer_lean_candidate_client_tool_workspace(
        proposal_agent=agent,
        question=question,
        task=task,
        blackboard=blackboard,
        theory_packet={},
        environment_feedback=feedback,
        registered_problem={},
        theorem_goals=[],
        formal_source_retriever=None,
        proof_search_provider=None,
        proof_state_provider=proof_state_provider,
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
    assert agent.declaration_result["status"] == "OBSERVED"
    assert proof_state_provider.calls[0]["symbol"] == "Example.Source"
    inspected_path = proof_state_provider.calls[0]["artifact_path"]
    assert stable_hash(
        Path(inspected_path).read_text(encoding="utf-8")
    ) == stable_hash(source)

    indexed_source_path = tmp_path / "IndexedSource.lean"
    indexed_source_path.write_text(
        "namespace Example.Namespace\n\nstructure Source where\n  value : Nat\n\nend Example.Namespace\n",
        encoding="utf-8",
    )

    class IndexedDeclaration:
        name = "Example.Namespace.Source"
        namespace = "Example.Namespace"
        path = str(indexed_source_path)
        line = 3
        signature = "structure Source where"

    class IndexedHit:
        declaration = IndexedDeclaration()

    class IndexedRetriever:
        def search(self, symbol: str, *, k: int):
            assert symbol == "Example.Namespace.Source"
            assert k == 8
            return [IndexedHit()]

    indexed_agent = FakeAgent(
        inspection_symbol="Example.Namespace.Source",
    )
    indexed_provider = FakeProofStateProvider()
    indexed_result = (
        runtime_module._runtime_formalizer_lean_candidate_client_tool_workspace(
            proposal_agent=indexed_agent,
            question=question,
            task=task,
            blackboard=blackboard,
            theory_packet={},
            environment_feedback=feedback,
            registered_problem={},
            theorem_goals=[],
            formal_source_retriever=IndexedRetriever(),
            proof_search_provider=None,
            proof_state_provider=indexed_provider,
            lean_candidate_root=tmp_path / "indexed-candidates",
            lean_candidate_local_lean=True,
            lean_candidate_lean_project=tmp_path,
            lean_candidate_lean_timeout=5,
        )
    )

    assert indexed_result is not None
    assert indexed_provider.calls[0]["symbol"] == "Source"
    assert indexed_provider.calls[0]["artifact_path"] == str(indexed_source_path)
    assert indexed_agent.declaration_result["requested_symbol"] == (
        "Example.Namespace.Source"
    )
    assert indexed_agent.declaration_result["inspected_source_symbol"] == "Source"
    assert indexed_agent.declaration_result["indexed_declaration_namespace"] == (
        "Example.Namespace"
    )
    assert indexed_agent.declaration_result["indexed_declaration_line"] == 3
    assert indexed_agent.declaration_result["indexed_declaration_signature"] == (
        "structure Source where"
    )
    assert indexed_agent.declaration_result[
        "indexed_symbol_context_observed"
    ] is True
    assert "structure Source where" in indexed_agent.declaration_result[
        "indexed_source_context"
    ]["content"]

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
    resumed = runtime_module._runtime_formalizer_lean_candidate_client_tool_workspace(
        proposal_agent=FakeAgent(resumed_source),
        question=question,
        task=task,
        blackboard=blackboard,
        theory_packet={},
        environment_feedback=resume_feedback,
        registered_problem={},
        theorem_goals=[],
        formal_source_retriever=None,
        proof_search_provider=None,
        proof_state_provider=proof_state_provider,
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
        runtime_module._runtime_formalizer_lean_candidate_client_tool_workspace(
            proposal_agent=FakeAgent(resumed_source),
            question=question,
            task=task,
            blackboard=blackboard,
            theory_packet={},
            environment_feedback=stale_feedback,
            registered_problem={},
            theorem_goals=[],
            formal_source_retriever=None,
            proof_search_provider=None,
            proof_state_provider=proof_state_provider,
            lean_candidate_root=tmp_path / "candidates",
            lean_candidate_local_lean=True,
            lean_candidate_lean_project=tmp_path,
            lean_candidate_lean_timeout=5,
        )
    except PacketValidationError as exc:
        assert exc.validation_label == "Lean workspace checkpoint lineage"
    else:
        raise AssertionError("stale model checkpoint source was not rejected")


def test_formalizer_subsystem_replaces_initial_source_packet_with_direct_workspace(
    tmp_path,
    monkeypatch,
) -> None:
    question = OpenResearchQuestion(
        id="canonical-initial-formalizer",
        title="Canonical initial Formalizer",
        description="Author exact initial Lean source through client tools.",
    )
    theory_packet_id = "theory:canonical-initial-formalizer"
    theory_packet = {
        "packet_id": theory_packet_id,
        "artifact_kind": "TheoryDerivationPacket",
        "problem_card": {
            "observed_data": "One arbitrary real value.",
            "estimand": "The unchanged exact identity.",
            "assumptions": [],
        },
        "theorem_cards": [
            {
                "id": "goal-1",
                "title": "Exact goal",
                "informal_statement": "The exact unchanged theorem target.",
                "conclusion": "The exact unchanged theorem target.",
                "proof_strategy": "Formalize the identity directly.",
            }
        ],
        "formalization_requests": [
            {
                "id": "formalize-goal-1",
                "target_theorem_card": "goal-1",
                "semantic_alignment_constraints": [
                    "Preserve the exact target."
                ],
            }
        ],
        "theory_derivation_packet": {
            "formalization_handoff": {
                "source_theorem_target": "goal-1",
                "semantic_alignment_constraints": [
                    "Preserve the exact target."
                ],
            }
        },
    }
    draft = (
        "theorem Exact.target : True := by\n"
        "  exact False.elim (by contradiction)\n"
    )
    authored = "theorem Exact.target : True := by\n  exact True.intro\n"
    project_source = tmp_path / "Project.lean"
    project_source.write_text(
        "theorem Project.Source : True := by exact True.intro\n",
        encoding="utf-8",
    )

    class FormalSourceRetriever:
        def search(self, query, *, k):
            assert query == "Project.Source"
            assert k == 8

            class Declaration:
                name = "Project.Source"
                path = "Project.lean"

            class Hit:
                declaration = Declaration()

            return [Hit()]

    class ProofStateProvider:
        name = "fake_lean_lsp_mcp"

        def __init__(self) -> None:
            self.calls = []

        def inspect_declaration(self, **kwargs):
            self.calls.append(dict(kwargs))
            return {
                "ok": True,
                "status": "OBSERVED",
                "executed_tools": ["lean_lsp_mcp.lean_declaration_file"],
                "symbol": kwargs["symbol"],
                "proof_evidence_status": (
                    "LEAN_DECLARATION_INSPECTION_NOT_PROOF_EVIDENCE"
                ),
            }

    class FormalizerBackend(ScriptedLeanToolBackend):
        def __init__(self) -> None:
            super().__init__(
                [
                    _response(
                        ClientToolCall(
                            "inspect-before-source",
                            "inspect_lean_declaration",
                            {"symbol": "Project.Source"},
                        )
                    ),
                    _response(
                        ClientToolCall(
                            "submit-first-source",
                            LEAN_SOURCE_SUBMISSION_TOOL,
                            {
                                "lean_source": draft,
                                "candidate_declaration_name": "Exact.target",
                            },
                        )
                    ),
                    _response(
                        ClientToolCall(
                            "inspect-after-source",
                            "inspect_lean_declaration",
                            {"symbol": "Project.Source"},
                        )
                    ),
                    _response(
                        ClientToolCall(
                            "submit-revised-source",
                            LEAN_SOURCE_SUBMISSION_TOOL,
                            {
                                "lean_source": authored,
                                "candidate_declaration_name": "Exact.target",
                            },
                        )
                    ),
                ]
            )

    def fake_local_check(**kwargs):
        submitted = Path(kwargs["artifact_path"]).read_text(encoding="utf-8")
        compiled = submitted == authored
        return {
            "local_lean_attempted": True,
            "local_lean_compiled": compiled,
            "local_lean_source_compiled": compiled,
            "local_lean_exit_status": "0" if compiled else "1",
            "local_lean_stdout": (
                "Exact.target : True" if compiled else "type mismatch"
            ),
            "local_lean_stderr": "",
            "candidate_identity_lean_checked": compiled,
            "candidate_identity_lean_verified": compiled,
        }

    monkeypatch.setattr(
        runtime_module,
        "_run_formalizer_lean_candidate_local_check",
        fake_local_check,
    )
    backend = FormalizerBackend()
    agent = LLMFormalizerProofEngineerAgent(
        provider=backend,
        config=FormalizerConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            max_validation_retries=0,
            client_tool_lean_candidate_max_turns=4,
            client_tool_lean_candidate_max_no_progress_turns=1,
        ),
    )
    proof_state_provider = ProofStateProvider()
    subsystem = runtime_module.FormalizerWorkspaceRuntimeSubsystem(
        proposal_agent=agent,
        proof_state_provider=proof_state_provider,
        formal_source_retriever=FormalSourceRetriever(),
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=tmp_path,
        formal_target_semantic_reviewer_available=False,
    )
    task = AgentTask(
        task_id="formalize:canonical-initial",
        owner_subsystem="FormalizationEvaluator",
        objective="Author one exact target.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": {},
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={theory_packet_id: theory_packet},
    )
    result = subsystem.run(task, blackboard)

    assert all(
        row.get("artifact_kind") != "FormalizerTargetBindingPacket"
        for row in result.produced_artifacts.values()
    )
    assert len(backend.requests) == 4
    assert "at most 4 model-tool turns" in backend.requests[0].system_prompt
    assert proof_state_provider.calls == [
        {
            "artifact_path": str(project_source),
            "symbol": "Project.Source",
            "context_lines": 20,
        },
        {
            "artifact_path": str(project_source),
            "symbol": "Project.Source",
            "context_lines": 20,
        },
    ]
    proposals = [
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "FormalizerProofEngineerProposalPacket"
    ]
    assert len(proposals) == 1
    assert proposals[0]["formal_targets"][0]["lean_statement_sketch"] == authored
    workspaces = [
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "LeanCandidateClientToolWorkspace"
    ]
    assert len(workspaces) == 1
    assert workspaces[0]["workspace_phase"] == "initial_authoring"
    assert workspaces[0]["lean_declaration_inspections"] == 2
    assert workspaces[0]["local_lean_checks"] == 2
    assert workspaces[0]["lean_lsp_mcp_live_called"] is True
    assert workspaces[0]["runtime_selected_lean_code"] is False
    assert result.status == "BLOCKED"
    assert result.failure_classification == "formalizer_workspace_exhausted"
    assert result.next_task is None
    assert "no independent exact-target reviewer is available" in result.rationale


def test_formalizer_subsystem_records_direct_workspace_gap_without_packet_failure(
    tmp_path,
    monkeypatch,
) -> None:
    question = OpenResearchQuestion(
        id="canonical-formal-gap",
        title="Canonical direct Formalizer gap",
        description="Record a concrete missing formal foundation without proof credit.",
    )
    theory_packet_id = "theory:canonical-formal-gap"
    theory_packet = {
        "packet_id": theory_packet_id,
        "artifact_kind": "TheoryDerivationPacket",
        "problem_card": {"estimand": "an exact generic target"},
        "theorem_cards": [],
        "formalization_requests": [],
    }
    formal_gap = {
        "summary": "The active project lacks the required project lemma.",
        "missing_primitives": ["Project.requiredLemma"],
        "blocking_observations": ["The attempted source retained sorryAx."],
    }
    proposal = {
        "schema_version": 1,
        "artifact_kind": "FormalizerProofEngineerProposalPacket",
        "packet_id": "formalizer-proposal:canonical-formal-gap",
        "source_agent": "LLMFormalizerProofEngineerAgent",
        "provider": "anthropic",
        "provider_name": "anthropic",
        "backend_provider": "anthropic",
        "backend_provider_name": "anthropic",
        "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "model_tier": "haiku",
        "formal_targets": [
            {
                "id": "exact-target",
                "formal_target_role": (
                    FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP
                ),
                "lean_statement_sketch": "",
                "candidate_lean_declaration": "",
                "lean_imports": [],
                "expected_status": "FORMAL_GAP",
                "formal_gap": formal_gap,
            }
        ],
        "retrieval_queries": [],
        "gap_taxonomy": [formal_gap],
    }
    workspace = {
        "schema_version": 1,
        "artifact_kind": "LeanCandidateClientToolWorkspace",
        "disposition": "FORMAL_GAP",
        "candidate_id": "exact-target",
        "submitted_source_hash": stable_hash(
            "theorem exact_target : True := by sorry\n"
        ),
        "source_updates": 1,
        "formal_environment_searches": 2,
        "proof_candidate_searches": 1,
        "local_lean_checks": 1,
        "latest_check_compiled": True,
        "model_explicit_submit": True,
        "model_owned_lean_code": True,
        "runtime_selected_lean_code": False,
        "independent_semantic_review_required": False,
        "kernel_verified": False,
        "proof_evidence_status": (
            "MODEL_REPORTED_FORMAL_GAP_NOT_PROOF_EVIDENCE"
        ),
    }

    monkeypatch.setattr(
        runtime_module,
        "_runtime_formalizer_client_tool_workspace_available",
        lambda **_kwargs: True,
    )
    monkeypatch.setattr(
        runtime_module,
        "_runtime_formalizer_lean_candidate_client_tool_workspace",
        lambda **_kwargs: (proposal, workspace),
    )
    subsystem = runtime_module.FormalizerWorkspaceRuntimeSubsystem(
        proposal_agent=object(),
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_local_lean=True,
        lean_candidate_lean_project=tmp_path,
        formal_target_semantic_reviewer_available=False,
    )
    task = AgentTask(
        task_id="formalize:canonical-formal-gap",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the exact target or record a concrete gap.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": {
                "runtime_requested_evidence_contract": {
                    "formal_evaluation_requires_formalizer_lean_candidate": True
                }
            },
        },
    )

    result = subsystem.run(
        task,
        BlackboardState(
            project_id=question.id,
            artifacts={theory_packet_id: theory_packet},
        ),
    )

    assert result.status == "REROUTE"
    assert result.failure_classification == ""
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert not any(
        observation.observation_type == "formalizer_packet_validation_failure"
        for observation in result.observations
    )
    manifest = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "RuntimeFormalizationManifest"
    )
    assert manifest["formalizer_reported_gap"] is True
    assert manifest["counts"]["formal_gap"] == 1
    assert manifest["source_theorem_kernel_verified"] is False
    workspace_artifact = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "LeanCandidateClientToolWorkspace"
    )
    assert workspace_artifact["model_owned_lean_code"] is True
    assert workspace_artifact["kernel_verified"] is False
    loop_evidence = next(
        row
        for row in result.evidence_entries
        if row.evidence_type == "formalizer_lean_candidate_client_tool_loop"
    )
    assert loop_evidence.payload["candidate_source_hash"] == workspace[
        "submitted_source_hash"
    ]
    assert loop_evidence.payload["n_formal_source_search_calls"] == 2
    assert loop_evidence.payload["n_proof_candidate_search_calls"] == 1
    assert loop_evidence.payload["n_formal_rag_tool_calls"] == 3


def test_formalizer_client_tool_revision_rebuilds_only_bound_candidate_source(
    monkeypatch,
) -> None:
    original = "import Missing.Module\n\ntheorem target : True := by trivial\n"
    repaired = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {"lean_source": repaired},
                )
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

    packet, evidence = agent.run_lean_candidate_workspace_with_client_tools(
        question=question,
        theory_packet={},
        parent_packet=parent_packet,
        candidate_id="target-candidate",
        candidate_source_field="formal_targets",
        candidate_lean_declaration="target",
        initial_source=original,
        environment_feedback=feedback,
        check_candidate=lambda source, _declaration: {
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
    assert backend.requests[0].metadata["client_tool_loop_max_turns"] == (
        FormalizerConfig().client_tool_lean_candidate_max_turns
    )

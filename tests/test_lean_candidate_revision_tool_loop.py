from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_statistician.client_tool_loop import (
    CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY,
    CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY,
    CLIENT_TOOL_TRANSCRIPT_POLICY,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.agent_runtime import (
    AgentTask,
    BlackboardState,
    RUNTIME_CONTINUATION_BUDGET_MARKER_KEY,
)
from ai_statistician.lean_candidate_revision_tool_loop import (
    LEAN_CANDIDATE_WORKSPACE_CHECKPOINT_KIND,
    LEAN_FORMAL_GAP_TOOL,
    LEAN_SCRATCH_TOOL,
    LEAN_SUPPORT_FILE_CHECK_TOOL,
    LEAN_SUPPORT_FILE_WRITE_TOOL,
    LEAN_SOURCE_EDIT_TOOL,
    LEAN_SOURCE_READ_TOOL,
    LEAN_SOURCE_SUBMISSION_TOOL,
    lean_candidate_workspace_continuation_errors,
    run_lean_candidate_revision_tool_loop,
    seal_lean_candidate_workspace_checkpoint,
)
from ai_statistician.lean_project import (
    load_model_authored_lean_project,
    model_authored_lean_project,
    persist_model_authored_lean_project,
)
from ai_statistician.lean_candidate_identity import (
    TRUSTED_LEAN_AXIOMS,
    _lean_axioms_from_report,
    run_lean_candidate_identity_probe,
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
from ai_statistician.research_schema import (
    OpenResearchQuestion,
    research_workspace_authorization_fingerprint,
)
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
    THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    theory_workspace_document_manifest,
)
from ai_statistician import (
    lean_candidate_revision_tool_loop as lean_candidate_tool_loop_module,
)
import ai_statistician.formalizer_llm as formalizer_module
import ai_statistician.lean_candidate_identity as lean_identity_module
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


def _initial_workspace(request: ClientToolTurnRequest) -> dict:
    marker = "Initial authoritative Lean workspace state:\n"
    for message in reversed(request.messages):
        content = message.get("content", "")
        blocks = (
            [content]
            if isinstance(content, str)
            else [
                str(block.get("text", "") or "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            if isinstance(content, list)
            else []
        )
        for block in reversed(blocks):
            if marker in block:
                return json.loads(block.split(marker, 1)[1])
    raise AssertionError("Lean workspace state is missing from the request")


def _lean_workspace_checkpoint(
    *,
    parent_source: str,
    current_source: str,
    candidate_id: str = "target-candidate",
    declaration: str = "target",
    searches: int = 0,
    resumed_from_checkpoint_id: str = "",
    prior_checkpoint: dict | None = None,
) -> dict:
    check = {
        "source_hash": stable_hash(current_source),
        "compiled": False,
        "local_lean_stderr": "type mismatch",
    }
    check_fingerprint = "lean-check:" + stable_hash(
        {
            "source_hash": stable_hash(current_source),
            "candidate_lean_declaration": declaration,
            "check_result": check,
        }
    )
    prior_fingerprints = list(
        (prior_checkpoint or {}).get("workspace_observation_fingerprints", [])
    )
    fingerprints = sorted(
        set(prior_fingerprints)
        | {check_fingerprint}
        | ({"search:test-observation"} if searches else set())
    )
    prior_counters = {
        field: int((prior_checkpoint or {}).get(field, 0) or 0)
        for field in (
            "source_updates",
            "declaration_updates",
            "source_reads",
            "searches",
            "proof_searches",
            "state_inspections",
            "declaration_inspections",
            "checks",
        )
    }
    body = {
        "schema_version": 2,
        "artifact_kind": LEAN_CANDIDATE_WORKSPACE_CHECKPOINT_KIND,
        "candidate_id": candidate_id,
        "parent_candidate_lean_declaration": declaration,
        "candidate_lean_declaration": declaration,
        "workspace_phase": "revision" if parent_source else "initial_authoring",
        "parent_source_hash": stable_hash(parent_source),
        "rejected_source_hash": "",
        "current_source_hash": stable_hash(current_source),
        "current_source": current_source,
        "checked_candidate_keys": [
            {
                "source_hash": stable_hash(current_source),
                "candidate_lean_declaration": declaration,
            }
        ],
        "workspace_observation_fingerprints": fingerprints,
        "source_updates": max(1, prior_counters["source_updates"]),
        "declaration_updates": prior_counters["declaration_updates"],
        "source_reads": prior_counters["source_reads"],
        "searches": max(searches, prior_counters["searches"]),
        "proof_searches": prior_counters["proof_searches"],
        "state_inspections": prior_counters["state_inspections"],
        "declaration_inspections": prior_counters["declaration_inspections"],
        "checks": 1,
        "segment_start_counters": prior_counters,
        "segment_start_observation_count": len(prior_fingerprints),
        "last_check": check,
        "last_check_hash": stable_hash(check),
        "latest_check_observation": check,
        "latest_formal_environment_search": {},
        "latest_proof_search": {},
        "latest_state_inspection": {},
        "latest_declaration_inspection": {},
        "resumed_from_checkpoint_id": resumed_from_checkpoint_id,
        "turns": 1,
        "tool_calls": 1 + int(bool(searches)),
        "interaction_policy": "single_model_tool_observation_budget_v1",
        "transcript_fingerprint": "test-transcript",
        "provider": "anthropic",
        "model": DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        "model_tier": "haiku",
        "resumable": len(fingerprints) > len(prior_fingerprints),
        "accepted": False,
        "runtime_selected_lean_code": False,
        "model_owned_lean_code": True,
        "model_owned_workspace_actions": (
            len(fingerprints) > len(prior_fingerprints)
        ),
        "kernel_verified": False,
        "proof_evidence_status": (
            "CLIENT_TOOL_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    return seal_lean_candidate_workspace_checkpoint(body)


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


def test_identity_probe_separates_elaboration_from_untrusted_proof(
    tmp_path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "Candidate.lean"
    source_path.write_text(
        "namespace Candidate\ntheorem target : True := by\n  sorry\nend Candidate\n",
        encoding="utf-8",
    )

    class Completed:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    responses = [
        Completed(0),
        Completed(
            0,
            "Candidate.target : True\n"
            "'Candidate.target' depends on axioms: [sorryAx]",
        ),
    ]
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(list(command))
        assert kwargs["check"] is False
        assert kwargs["capture_output"] is True
        return responses.pop(0)

    monkeypatch.setattr(lean_identity_module.subprocess, "run", fake_run)

    result = run_lean_candidate_identity_probe(
        artifact_path=source_path,
        candidate_lean_declaration="Candidate.target",
        lean_project=tmp_path,
    )

    assert len(commands) == 2
    assert result["local_lean_source_compiled"] is True
    assert result["local_lean_compiled"] is False
    assert result["candidate_declaration_elaborated"] is True
    assert result["candidate_development_status"] == (
        "DECLARATION_ELABORATED_PROOF_UNTRUSTED"
    )
    assert result["candidate_identity_lean_verified"] is False
    assert result["candidate_untrusted_axiom_names"] == ["sorryAx"]
    assert result["candidate_axiom_audit_clean"] is False


def test_formalizer_prompt_exposes_model_owned_scratch_without_proof_promotion() -> None:
    assert "scratch experiment" in formalizer_module.FORMALIZER_SYSTEM_PROMPT
    assert "admitted or diagnostic source as proof" in (
        formalizer_module.FORMALIZER_SYSTEM_PROMPT
    )
    submit_tool = next(
        tool
        for tool in lean_candidate_tool_loop_module._lean_candidate_revision_tools()
        if tool.name == LEAN_SOURCE_SUBMISSION_TOOL
    )
    scratch_tool = next(
        tool
        for tool in lean_candidate_tool_loop_module._lean_candidate_revision_tools()
        if tool.name == LEAN_SCRATCH_TOOL
    )
    assert "#check" in scratch_tool.description
    assert "without changing the current candidate" in scratch_tool.description
    assert "never proof" in scratch_tool.description
    assert "complete axiom-clean declaration" in submit_tool.description


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
                    {
                        "lean_source": repaired,
                        "candidate_declaration_name": "target",
                    },
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
    assert all(request.enable_prompt_caching for request in backend.requests)
    assert set(tool.name for tool in backend.requests[0].tools) == {
        LEAN_SOURCE_EDIT_TOOL,
        LEAN_SOURCE_READ_TOOL,
        LEAN_SCRATCH_TOOL,
        LEAN_SOURCE_SUBMISSION_TOOL,
        "search_formal_environment",
    }
    assert all(
        request.disable_parallel_tool_use is False
        for request in backend.requests
    )
    initial_workspace = _initial_workspace(backend.requests[0])
    assert "current_lean_source" not in initial_workspace
    assert initial_workspace["current_source_manifest"] == {
        "source_hash": stable_hash(initial),
        "line_count": 3,
        "character_count": len(initial),
        "source_present": True,
        "complete_source_inline": False,
        "content_transport": LEAN_SOURCE_READ_TOOL,
    }
    assert initial not in json.dumps(backend.requests[0].messages)
    assert initial_workspace["latest_check_observation"][
        "local_lean_stderr"
    ] == "unknown module"
    assert result.evidence["handoff_mode"] == (
        "successful_model_source_submission"
    )
    assert result.evidence["model_explicit_submit"] is True
    assert result.evidence["submit_and_check_atomic"] is True


def test_lean_candidate_tool_loop_accepts_model_revised_support_project(
    tmp_path: Path,
) -> None:
    target = (
        "import AIStatWorkspace.Support\n\n"
        "theorem target : True := by exact AIStatWorkspace.support_true\n"
    )
    support_path = "AIStatWorkspace/Support.lean"
    old_support = (
        "namespace AIStatWorkspace\n"
        "theorem support_true : True := by trivial\n"
        "end AIStatWorkspace\n"
    )
    new_support = old_support.replace("by trivial", "by exact True.intro")
    initial_project = model_authored_lean_project(
        target_source=target,
        project_files=[{"path": support_path, "content": old_support}],
        support_build_order=(support_path,),
    )
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "replace-support",
                    LEAN_SUPPORT_FILE_WRITE_TOOL,
                    {"path": support_path, "content": new_support},
                )
            ),
            _response(
                ClientToolCall(
                    "check-support",
                    LEAN_SUPPORT_FILE_CHECK_TOOL,
                    {"path": support_path},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-target",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": target,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    checked_projects: list[tuple[list[dict], list[str]]] = []

    def check_project(source, declaration, files, order):
        assert source == target
        assert declaration == "target"
        checked_projects.append((list(files), list(order)))
        return {"source_hash": stable_hash(source), "compiled": True}

    def check_support(path, files, prior_order):
        assert path == support_path
        assert prior_order == []
        assert files[0]["content"] == new_support
        return {
            "relative_path": path,
            "source_hash": stable_hash(new_support),
            "compiled": True,
            "local_lean_stderr": "",
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise the rejected project.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=target,
        initial_lean_project=initial_project,
        check_candidate=lambda *_args: pytest.fail("single-file checker used"),
        check_candidate_project=check_project,
        check_support_file=check_support,
        search_formal_environment=lambda query, k: {"query": query, "hits": []},
        rejected_source_hash=stable_hash(target),
        rejected_lean_project_hash=initial_project["project_hash"],
        session_dir=tmp_path / "formalizer-session",
    )

    project_rows, project_order = load_model_authored_lean_project(
        result.lean_project,
        target_source=target,
    )
    assert result.lean_source == target
    assert result.lean_project["project_hash"] != initial_project["project_hash"]
    assert result.lean_project["artifact_kind"] == "ModelAuthoredLeanProjectRef"
    assert project_rows[0].content == new_support
    assert project_order == (support_path,)
    assert result.evidence["runtime_selected_lean_code"] is False
    assert result.evidence["lean_support_file_writes"] == 1
    assert result.evidence["lean_support_file_checks"] == 1
    assert len(checked_projects) == 2
    assert checked_projects[-1][1] == [support_path]


def test_lean_support_project_checkpoint_resumes_same_model_workspace() -> None:
    target = "import AIStat.Support\n\ntheorem target : True := by exact AIStat.helper\n"
    support_path = "AIStat/Support.lean"
    support_source = "namespace AIStat\ntheorem helper : True := by trivial\nend AIStat\n"

    def check_project(source, declaration, files, order):
        return {
            "source_hash": stable_hash(source),
            "candidate_lean_declaration": declaration,
            "compiled": bool(files and order == [support_path]),
        }

    def check_support(path, files, prior_order):
        assert path == support_path
        assert prior_order == []
        assert files[0]["content"] == support_source
        return {
            "relative_path": path,
            "source_hash": stable_hash(support_source),
            "compiled": True,
        }

    first_backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "write-support",
                    LEAN_SUPPORT_FILE_WRITE_TOOL,
                    {"path": support_path, "content": support_source},
                )
            )
        ]
    )
    with pytest.raises(PacketValidationError) as exc_info:
        run_lean_candidate_revision_tool_loop(
            provider=first_backend,
            system_prompt="Use tools.",
            user_prompt="Build the project.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=target,
            check_candidate=lambda *_args: pytest.fail("single-file checker used"),
            check_candidate_project=check_project,
            check_support_file=check_support,
            search_formal_environment=lambda query, k: {"query": query, "hits": []},
        )
    checkpoint = dict(exc_info.value.recovery_checkpoint)
    assert checkpoint["schema_version"] == 3
    assert checkpoint["support_files"][0]["content"] == support_source
    assert checkpoint["support_build_order"] == []
    assert checkpoint["resumable"] is True

    resumed_backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "check-support",
                    LEAN_SUPPORT_FILE_CHECK_TOOL,
                    {"path": support_path},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-target",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": target,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    result = run_lean_candidate_revision_tool_loop(
        provider=resumed_backend,
        system_prompt="Use tools.",
        user_prompt="Continue the project.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=target,
        check_candidate=lambda *_args: pytest.fail("single-file checker used"),
        check_candidate_project=check_project,
        check_support_file=check_support,
        search_formal_environment=lambda query, k: {"query": query, "hits": []},
        recovery_checkpoint=checkpoint,
    )

    assert result.lean_project["support_build_order"] == [support_path]
    assert result.evidence["resumed_from_checkpoint_id"] == checkpoint[
        "checkpoint_id"
    ]


def test_lean_candidate_tool_loop_applies_exact_model_edit_and_checks_full_source() -> None:
    initial = "-- pending\ntheorem target : True := by\n  exact missing_name\n"
    revised = "-- checked\ntheorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "edit-current-source",
                    LEAN_SOURCE_EDIT_TOOL,
                    {"edits": [
                        {"old_text": "-- pending", "new_text": "-- checked"},
                        {
                            "old_text": "exact missing_name",
                            "new_text": "exact True.intro",
                        },
                    ]},
                )
            )
        ]
    )
    checked_sources: list[str] = []

    def check(source: str, declaration: str):
        checked_sources.append(source)
        return {
            "source_hash": stable_hash(source),
            "candidate_lean_declaration": declaration,
            "compiled": source == revised,
            "local_lean_stderr": (
                "unknown identifier 'missing_name'" if source == initial else ""
            ),
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Revise this exact current source from Lean feedback.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
    )

    assert checked_sources == [initial, revised]
    assert result.lean_source == revised
    assert result.source_hash == stable_hash(revised)
    assert result.evidence["source_updates"] == 1
    assert result.evidence["local_lean_checks"] == 2
    assert result.evidence["terminal_source_action"] == "atomic_exact_text_edits"
    assert result.evidence["model_owned_lean_code"] is True
    assert result.evidence["runtime_selected_lean_code"] is False
    assert result.evidence["independent_semantic_review_required"] is True
    assert result.evidence["runtime_kernel_promotion_required"] is True
    assert result.evidence["kernel_verified"] is False
    edit_tool = next(
        tool
        for tool in backend.requests[0].tools
        if tool.name == LEAN_SOURCE_EDIT_TOOL
    )
    assert edit_tool.terminal is True
    assert edit_tool.input_schema["required"] == ["edits"]
    assert "ordered atomic batch" in edit_tool.description


def test_lean_candidate_tool_loop_reads_hash_bound_source_before_exact_edit() -> None:
    initial = (
        "-- source-visible-only-through-read\n"
        "theorem target : True := by\n"
        "  exact missing_name\n"
    )
    revised = initial.replace("exact missing_name", "exact True.intro")
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "read-current-source",
                    LEAN_SOURCE_READ_TOOL,
                    {"line_start": 1, "line_end": 3},
                )
            ),
            _response(
                ClientToolCall(
                    "edit-current-source",
                    LEAN_SOURCE_EDIT_TOOL,
                    {"edits": [{
                        "old_text": "exact missing_name",
                        "new_text": "exact True.intro",
                    }]},
                )
            ),
        ]
    )
    checked_sources: list[str] = []

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Read the retained source before a localized edit.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=lambda source, _declaration: (
            checked_sources.append(source)
            or {
                "source_hash": stable_hash(source),
                "compiled": source == revised,
                "local_lean_stderr": (
                    "unknown identifier 'missing_name'"
                    if source == initial
                    else ""
                ),
            }
        ),
        search_formal_environment=lambda query, k: [],
    )

    opening_context = json.dumps(backend.requests[0].messages, sort_keys=True)
    read_context = json.dumps(backend.requests[1].messages, sort_keys=True)
    assert "source-visible-only-through-read" not in opening_context
    assert "source-visible-only-through-read" in read_context
    assert stable_hash(initial) in read_context
    assert checked_sources == [initial, revised]
    assert result.lean_source == revised
    assert result.evidence["current_source_reads"] == 1
    assert result.evidence["current_source_read_available"] is True
    assert result.evidence["current_source_content_transport"] == (
        LEAN_SOURCE_READ_TOOL
    )
    persisted_history = json.dumps(result.evidence["history"], sort_keys=True)
    assert "source-visible-only-through-read" not in persisted_history
    assert "current model-owned source content omitted" in persisted_history


def test_lean_candidate_tool_loop_returns_ambiguous_edit_error_to_same_model() -> None:
    initial = (
        "-- missing_name is intentionally mentioned here\n"
        "theorem target : True := by\n"
        "  exact missing_name\n"
    )
    revised = initial.replace("exact missing_name", "exact True.intro")
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "ambiguous-edit",
                    LEAN_SOURCE_EDIT_TOOL,
                    {"edits": [{
                        "old_text": "missing_name",
                        "new_text": "True.intro",
                    }]},
                )
            ),
            _response(
                ClientToolCall(
                    "unique-edit",
                    LEAN_SOURCE_EDIT_TOOL,
                    {"edits": [{
                        "old_text": "exact missing_name",
                        "new_text": "exact True.intro",
                    }]},
                )
            ),
        ]
    )
    checked_sources: list[str] = []

    def check(source: str, _declaration: str):
        checked_sources.append(source)
        return {
            "source_hash": stable_hash(source),
            "compiled": source == revised,
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Edit the exact current source.",
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
    )

    assert checked_sources == [initial, revised]
    assert result.lean_source == revised
    assert result.evidence["runtime_executed_tool_calls"] == 2
    second_request_context = json.dumps(
        backend.requests[1].messages,
        sort_keys=True,
    )
    assert "observed 2 matches" in second_request_context
    assert "old_text must match the exact current artifact once" in (
        second_request_context
    )


def test_exact_lean_source_edit_rejects_overlapping_matches() -> None:
    with pytest.raises(ValueError, match="observed 2 matches"):
        lean_candidate_tool_loop_module._apply_exact_source_edit(
            "aaa",
            edits=[{"old_text": "aa", "new_text": "b"}],
        )


def test_lean_candidate_tool_loop_continues_checkpoint_with_exact_edit() -> None:
    parent = "theorem target : True := by\n  sorry\n"
    current = "theorem target : True := by\n  exact missing_name\n"
    revised = "theorem target : True := by\n  exact True.intro\n"
    checkpoint = _lean_workspace_checkpoint(
        parent_source=parent,
        current_source=current,
    )
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "continued-edit",
                    LEAN_SOURCE_EDIT_TOOL,
                    {"edits": [{
                        "old_text": "exact missing_name",
                        "new_text": "exact True.intro",
                    }]},
                )
            )
        ]
    )
    checked_sources: list[str] = []

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Continue the same exact workspace.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=parent,
        check_candidate=lambda source, _declaration: (
            checked_sources.append(source)
            or {"source_hash": stable_hash(source), "compiled": source == revised}
        ),
        search_formal_environment=lambda query, k: [],
        recovery_checkpoint=checkpoint,
    )

    assert checked_sources == [revised]
    continued_workspace = _initial_workspace(backend.requests[0])
    assert "current_lean_source" not in continued_workspace
    assert continued_workspace["current_source_manifest"]["source_hash"] == (
        stable_hash(current)
    )
    assert result.lean_source == revised
    assert result.evidence["resumed_from_checkpoint_id"] == checkpoint[
        "checkpoint_id"
    ]
    assert result.evidence["source_updates"] == 2
    assert result.evidence["workspace_segment_start_counters"][
        "source_updates"
    ] == 1


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


def test_model_can_correct_declaration_identity_without_rewriting_source() -> None:
    authored = (
        "namespace Example\n\n"
        "theorem target : True := by exact True.intro\n\n"
        "end Example\n"
    )
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-unqualified-identity",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": authored,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-qualified-identity",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": authored,
                        "candidate_declaration_name": "Example.target",
                    },
                )
            ),
        ]
    )
    checked: list[tuple[str, str]] = []

    def check(source: str, declaration: str):
        checked.append((source, declaration))
        compiled = declaration == "Example.target"
        return {
            "source_hash": stable_hash(source),
            "compiled": compiled,
            "local_lean_source_compiled": True,
            "candidate_identity_lean_verified": compiled,
            "candidate_identity_lean_stderr": (
                "Unknown identifier `target`" if not compiled else ""
            ),
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Author the exact target and identify its declaration.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source="",
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
    )

    assert checked == [(authored, "target"), (authored, "Example.target")]
    assert result.lean_source == authored
    assert result.candidate_lean_declaration == "Example.target"
    assert result.evidence["source_updates"] == 1
    assert result.evidence["declaration_updates"] == 1


def test_formal_gap_tool_keeps_model_authored_errors_in_source_revision_loop() -> None:
    failing = "theorem target : Missing.Type := by\n  sorry\n"
    passing = "theorem target : True := by\n  exact True.intro\n"
    tools = lean_candidate_tool_loop_module._lean_candidate_revision_tools(
        include_formal_gap=True,
    )
    gap_tool = next(tool for tool in tools if tool.name == LEAN_FORMAL_GAP_TOOL)
    assert "model-authored source are revision feedback" in gap_tool.description
    assert "existing target statement must elaborate first" in gap_tool.description
    assert "terminal result is not proof" in gap_tool.description

    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "premature-gap",
                    LEAN_FORMAL_GAP_TOOL,
                    {
                        "summary": "The active project lacks Missing.Type.",
                        "missing_primitives": ["Missing.Type"],
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-passing",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": passing,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )

    def check(source: str, _declaration: str):
        compiled = source == passing
        return {
            "source_hash": stable_hash(source),
            "compiled": compiled,
            "local_lean_source_compiled": compiled,
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Formalize the exact target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=failing,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        allow_formal_gap=True,
    )

    assert result.disposition == "AUTHOR_LEAN"
    assert result.lean_source == passing
    assert result.evidence["local_lean_checks"] == 2
    recovery_context = json.dumps(backend.requests[1].messages, sort_keys=True)
    assert "cannot promote an unelaborated model-authored source" in recovery_context


def test_lean_candidate_workspace_lets_model_report_task_bound_formal_gap() -> None:
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "search-required-primitive",
                    "search_formal_environment",
                    {"query": "Required.Primitive"},
                )
            ),
            _response(
                ClientToolCall(
                    "report-gap",
                    LEAN_FORMAL_GAP_TOOL,
                    {
                        "summary": "The active project lacks the required primitive.",
                        "missing_primitives": ["Required.Primitive"],
                        "blocking_observations": [
                            "The active-project search returned no matching declaration."
                        ],
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
    assert result.evidence["formal_environment_searches"] == 1


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
    gap_observation = result.evidence["formal_gap_observation"]
    assert gap_observation["current_source"] == attempted
    assert gap_observation["current_source_hash"] == stable_hash(attempted)
    assert gap_observation["candidate_lean_declaration"] == "target"
    assert gap_observation["latest_check_observation"][
        "local_lean_stderr"
    ].endswith("[sorryAx]")
    assert gap_observation["runtime_selected_lean_code"] is False
    assert gap_observation["kernel_verified"] is False


def test_formalizer_agent_keeps_formal_gap_available_after_workspace_resume() -> None:
    source = "theorem target : True := by\n  sorry\n"
    tool_environment_identity = {
        "lean_project": "/project/lean",
        "formal_source_retriever": {
            "source_snapshot_identities": {
                "statlib": {"git_commit": "statlib-active"}
            }
        },
    }
    question = OpenResearchQuestion(
        id="resumed-gap",
        title="Resume an exact target",
        description="Continue the same target or report a concrete gap.",
    )
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
        question=question,
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
            "local_lean_source_compiled": True,
            "local_lean_stderr": "target depends on axioms: [sorryAx]",
        },
        search_formal_environment=lambda query, k: [],
        tool_environment_identity=tool_environment_identity,
    )

    assert LEAN_FORMAL_GAP_TOOL in {
        tool.name for tool in backend.requests[0].tools
    }
    assert "your own submitted source is revision feedback" in (
        backend.requests[0].system_prompt
    )
    assert "inspected declaration source" in backend.requests[0].system_prompt
    assert "prioritize a model-authored exact edit" in (
        backend.requests[0].system_prompt
    )
    assert evidence["disposition"] == "FORMAL_GAP"
    assert evidence["local_lean_checks"] == 1
    assert evidence["model_explicit_submit"] is False
    assert evidence["model_owned_lean_code"] is True
    assert evidence["kernel_verified"] is False
    request_metadata = backend.requests[0].metadata
    assert request_metadata["formal_tool_environment_fingerprint"] == (
        stable_hash(tool_environment_identity)
    )
    assert request_metadata[
        CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY
    ] == research_workspace_authorization_fingerprint(
        question,
        {},
        {
            "subsystem": "FormalizationEvaluator",
            "candidate_id": "target-candidate",
            "theory_document_set_hash": "",
            "tool_environment_fingerprint": stable_hash(
                tool_environment_identity
            ),
        },
    )
    assert request_metadata[
        CLIENT_TOOL_AUTHORIZATION_FINGERPRINT_METADATA_KEY
    ] != research_workspace_authorization_fingerprint(
        question,
        {},
        {
            "subsystem": "FormalizationEvaluator",
            "candidate_id": "target-candidate",
            "theory_document_set_hash": "",
            "tool_environment_fingerprint": stable_hash({}),
        },
    )
    target = packet["formal_targets"][0]
    assert target["formal_target_role"] == (
        FORMAL_TARGET_ROLE_SOURCE_THEOREM_FORMAL_GAP
    )
    assert target["lean_statement_sketch"] == ""
    assert target["candidate_lean_declaration"] == ""
    assert target["formal_gap"]["missing_primitives"] == [
        "Project.requiredLemma"
    ]


def test_formalizer_reads_exact_theory_document_in_same_lean_session(
    tmp_path: Path,
) -> None:
    theory_content = (
        "# Exact claim\n\n"
        "UNIQUE_FORMALIZER_THEORY_BODY: for every n, the bound is finite.\n"
    )
    theory_root = tmp_path / "theory"
    theory_root.mkdir()
    (theory_root / "claim.md").write_text(theory_content, encoding="utf-8")
    theory_manifest = theory_workspace_document_manifest(
        {"claim.md": theory_content},
        workspace_dir=theory_root,
    )
    accepted = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "read-theory",
                    THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                    {"path": "claim.md", "line_start": 1, "line_end": 3},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-target",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": accepted,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
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
            id="document-grounded-formalizer",
            title="Formalize an exact document claim",
            description="Use the accepted Theory workspace as mathematical context.",
        ),
        theory_packet={
            "packet_id": "theory:document-grounded",
            "theory_workspace_manifest": theory_manifest,
        },
        parent_packet={
            "artifact_kind": "FormalizerWorkspaceTarget",
            "target_ref_id": "formalizer_workspace_target:document-grounded",
            "question_id": "document-grounded-formalizer",
            "formal_target": {
                "id": "target-candidate",
                "formal_target_role": "SOURCE_THEOREM_CANDIDATE",
                "informal_source": "The exact target is true.",
                "lean_statement_sketch": "",
                "candidate_lean_declaration": "",
                "lean_imports": [],
                "semantic_alignment_constraints": [
                    "Preserve the exact accepted Theory claim."
                ],
                "source_theorem_target_provenance": {
                    "source_theorem_goal_id": "goal-target",
                    "source_theorem_target_known": True,
                },
                "expected_status": "NEEDS_KERNEL_CHECK",
            },
        },
        candidate_id="target-candidate",
        candidate_source_field="formal_targets",
        candidate_lean_declaration="",
        initial_source="",
        environment_feedback={},
        check_candidate=lambda source, declaration: {
            "source_hash": stable_hash(source),
            "candidate_lean_declaration": declaration,
            "compiled": source == accepted and declaration == "target",
        },
        search_formal_environment=lambda query, k: [],
        session_dir=tmp_path / "lean-session",
    )

    first_request = backend.requests[0]
    first_request_text = first_request.system_prompt + str(first_request.messages)
    assert "UNIQUE_FORMALIZER_THEORY_BODY" not in first_request_text
    assert {
        THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
        THEORY_WORKSPACE_SEARCH_DOCUMENTS_TOOL,
    }.issubset({tool.name for tool in first_request.tools})
    initial_workspace = _initial_workspace(first_request)
    assert initial_workspace["authoritative_theory_documents"] == [
        {
            "path": "claim.md",
            "sha256": hashlib.sha256(theory_content.encode()).hexdigest(),
            "line_count": 3,
            "byte_size": len(theory_content.encode()),
        }
    ]
    assert initial_workspace["theory_document_content_transport"] == (
        "hash_bound_read_only_client_tools"
    )
    assert "UNIQUE_FORMALIZER_THEORY_BODY" in str(backend.requests[1].messages)
    assert packet["formal_targets"][0]["lean_statement_sketch"] == accepted
    assert evidence["authoritative_theory_documents"] == 1
    assert evidence["theory_document_inspections"] == 1
    assert evidence["theory_document_inspection_refs"][0][
        "proof_evidence_status"
    ] == "THEORY_DOCUMENT_INSPECTION_NOT_PROOF_EVIDENCE"
    assert "UNIQUE_FORMALIZER_THEORY_BODY" not in str(evidence)
    assert "workspace document content omitted" in str(evidence["history"])
    assert evidence["local_lean_checks"] == 1
    assert evidence["kernel_verified"] is False


def test_lean_workspace_rejects_changed_theory_documents_before_model_call() -> None:
    source = "theorem target : True := by\n  exact True.intro\n"
    original = "# Claim\n\nOriginal accepted mathematics.\n"
    changed = "# Claim\n\nChanged mathematics.\n"
    checkpoint = _lean_workspace_checkpoint(
        parent_source=source,
        current_source=source,
    )
    checkpoint = dict(checkpoint)
    checkpoint.pop("checkpoint_id")
    checkpoint["authoritative_theory_document_set_hash"] = stable_hash(
        [("claim.md", hashlib.sha256(original.encode()).hexdigest())]
    )
    checkpoint = seal_lean_candidate_workspace_checkpoint(checkpoint)
    backend = ScriptedLeanToolBackend([])

    with pytest.raises(PacketValidationError, match="Theory documents changed"):
        run_lean_candidate_revision_tool_loop(
            provider=backend,
            system_prompt="Use tools.",
            user_prompt="Continue the exact target.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=source,
            check_candidate=lambda current, declaration: {},
            search_formal_environment=lambda query, k: [],
            recovery_checkpoint=checkpoint,
            authoritative_theory_document_rows=[
                {
                    "path": "claim.md",
                    "sha256": hashlib.sha256(changed.encode()).hexdigest(),
                    "content": changed,
                }
            ],
        )

    assert backend.requests == []


def test_search_observation_reuses_retained_source_and_raw_lean_feedback() -> None:
    failing = "theorem target : True := by\n  exact missing\n"
    passing = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-failing",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": failing,
                        "candidate_declaration_name": "target",
                    },
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
                    {
                        "lean_source": passing,
                        "candidate_declaration_name": "target",
                    },
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
                    {
                        "query": "close target from current goal",
                        "openprover_task": {"context": [], "target": "True"},
                        "max_results": 2,
                        "lean_header": "import Mathlib\nopen scoped BigOperators\n",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": model_source,
                        "candidate_declaration_name": "target",
                    },
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
            {
                "source_hash": stable_hash(initial),
                "compiled": False,
                "model_lean_header": (
                    "import Mathlib\nopen scoped BigOperators\n"
                ),
                "model_openprover_task": {
                    "context": [],
                    "target": "True",
                },
            },
        )
    ]
    assert checked_sources == [initial, model_source]
    assert result.lean_source == model_source
    assert result.evidence["proof_candidate_searches"] == 1
    assert result.evidence["runtime_selected_lean_code"] is False
    assert result.evidence["model_owned_lean_code"] is True
    assert "search_proof_candidates" in result.evidence["tool_names"]


def test_proof_search_missing_model_selected_task_returns_to_same_formalizer() -> None:
    initial = "theorem target : True := by\n  exact missing\n"
    passing = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "proof-search-invalid",
                    "search_proof_candidates",
                    {"query": "close the current goal"},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-after-observation",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": passing,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    proof_search_calls = 0

    def search(_source: str, _query: str, _k: int, _context):
        nonlocal proof_search_calls
        proof_search_calls += 1
        raise AssertionError("invalid tool input must not reach the prover")

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Prove the exact target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=2,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=lambda source, _declaration: {
            "source_hash": stable_hash(source),
            "compiled": source == passing,
        },
        search_formal_environment=lambda query, k: [],
        search_proof_candidates=search,
    )

    first_observation = json.loads(
        backend.requests[1].messages[-1]["content"][0]["content"]
    )
    assert first_observation["error"] == "client_tool_input_rejected"
    assert "openprover_task" in first_observation["detail"]
    assert proof_search_calls == 0
    assert result.lean_source == passing


def test_proof_search_receives_only_current_hash_bound_lean_state() -> None:
    initial = "theorem target : True := by\n  exact missing\n"
    revised = "theorem target : True := by\n  exact still_missing\n"
    passing = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(ClientToolCall("state-1", "inspect_lean_state", {})),
            _response(
                ClientToolCall(
                    "proof-search-1",
                    "search_proof_candidates",
                    {
                        "query": "close the inspected goal",
                        "openprover_task": {
                            "context": [],
                            "target": "True",
                        },
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "revise-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": revised,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "proof-search-2",
                    "search_proof_candidates",
                    {
                        "query": "inspect the revised failure",
                        "openprover_task": {
                            "context": [],
                            "target": "True",
                        },
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "pass-1",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": passing,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    proof_search_contexts: list[dict] = []

    def check(source: str, _declaration: str):
        return {
            "source_hash": stable_hash(source),
            "compiled": source == passing,
            "local_lean_stderr": "unsolved goal" if source != passing else "",
        }

    def inspect(source: str, last_check):
        return {
            "status": "OBSERVED",
            "source_hash": stable_hash(source),
            "lean_project_hash": last_check.get("lean_project_hash", ""),
            "rows": [{"residual_goals": ["|- True"]}],
            "proof_evidence_status": "LEAN_STATE_INSPECTION_NOT_PROOF_EVIDENCE",
        }

    def search(_source: str, _query: str, _k: int, context):
        proof_search_contexts.append(dict(context))
        return {"source_theorem_candidate_proof_bodies": []}

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Inspect, search, and revise the exact source.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=6,
        max_no_progress_turns=3,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=initial,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        search_proof_candidates=search,
        inspect_lean_state=inspect,
    )

    first_state = proof_search_contexts[0]["latest_state_inspection"]
    assert first_state["source_hash"] == stable_hash(initial)
    assert first_state["rows"][0]["residual_goals"] == ["|- True"]
    assert "latest_state_inspection" not in proof_search_contexts[1]
    assert proof_search_contexts[1]["source_hash"] == stable_hash(revised)
    assert result.lean_source == passing


def test_model_selects_lean_state_inspection_inside_same_source_loop() -> None:
    initial = "theorem target : True := by\n  exact missing\n"
    revised = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-initial",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": initial,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(ClientToolCall("state-1", "inspect_lean_state", {})),
            _response(
                ClientToolCall(
                    "submit-revised",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": revised,
                        "candidate_declaration_name": "target",
                    },
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
            "source_hash": stable_hash(source),
            "lean_project_hash": last_check.get("lean_project_hash", ""),
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


def test_model_runs_lean_scratch_without_changing_candidate_source() -> None:
    scratch = "import Mathlib\n#check Missing.symbol\n"
    authored = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "scratch-1",
                    LEAN_SCRATCH_TOOL,
                    {"lean_source": scratch},
                )
            ),
            _response(
                ClientToolCall(
                    "submit-after-scratch",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": authored,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    checked: list[tuple[str, str]] = []

    def check(source: str, declaration: str):
        checked.append((source, declaration))
        scratch_run = not declaration
        return {
            "source_hash": stable_hash(source),
            "compiled": not scratch_run,
            "local_lean_source_compiled": not scratch_run,
            "local_lean_stdout": "unknown constant Missing.symbol"
            if scratch_run
            else "",
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Run a scratch experiment, then author the target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=3,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="",
        initial_source="",
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
    )

    assert checked == [(scratch, ""), (authored, "target")]
    assert result.lean_source == authored
    assert result.evidence["lean_scratch_checks"] == 1
    assert result.evidence["local_lean_checks"] == 1
    assert result.evidence["source_updates"] == 1
    history = json.dumps(result.evidence["history"], sort_keys=True)
    assert "LEAN_SCRATCH_NOT_PROOF_EVIDENCE" in history
    assert "candidate_source_unchanged" in history
    assert all(
        LEAN_SCRATCH_TOOL in {tool.name for tool in request.tools}
        for request in backend.requests
    )


def test_repeated_identical_lean_scratch_is_not_new_workspace_progress() -> None:
    scratch = "import Mathlib\n#check Missing.symbol\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    f"scratch-{index}",
                    LEAN_SCRATCH_TOOL,
                    {"lean_source": scratch},
                )
            )
            for index in range(2)
        ]
    )

    with pytest.raises(PacketValidationError) as raised:
        run_lean_candidate_revision_tool_loop(
            provider=backend,
            system_prompt="Use tools.",
            user_prompt="Inspect the exact target environment.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=5,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="",
            initial_source="",
            check_candidate=lambda source, _declaration: {
                "source_hash": stable_hash(source),
                "compiled": False,
                "local_lean_source_compiled": False,
                "local_lean_stderr": "unknown constant Missing.symbol",
            },
            search_formal_environment=lambda query, k: [],
        )

    checkpoint = raised.value.recovery_checkpoint
    assert raised.value.errors == ["repeated client-tool turns made no new progress"]
    assert raised.value.attempts == 2
    assert checkpoint["scratch_checks"] == 2
    assert len(
        [
            value
            for value in checkpoint["workspace_observation_fingerprints"]
            if value.startswith("lean-scratch:")
        ]
    ) == 1


def test_repeated_identical_failed_support_check_is_not_new_progress() -> None:
    target = "import AIStat.Support\n\ntheorem target : True := by trivial\n"
    support_path = "AIStat/Support.lean"
    support_source = "namespace AIStat\ntheorem helper : True := by missing\nend AIStat\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "write-support",
                    LEAN_SUPPORT_FILE_WRITE_TOOL,
                    {"path": support_path, "content": support_source},
                )
            ),
            *[
                _response(
                    ClientToolCall(
                        f"check-support-{index}",
                        LEAN_SUPPORT_FILE_CHECK_TOOL,
                        {"path": support_path},
                    )
                )
                for index in range(2)
            ],
        ]
    )

    with pytest.raises(PacketValidationError) as raised:
        run_lean_candidate_revision_tool_loop(
            provider=backend,
            system_prompt="Use tools.",
            user_prompt="Build the model-owned Lean project.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=6,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=target,
            check_candidate=lambda *_args: pytest.fail("single-file checker used"),
            check_candidate_project=lambda source, declaration, files, order: {
                "source_hash": stable_hash(source),
                "candidate_lean_declaration": declaration,
                "compiled": False,
            },
            check_support_file=lambda path, files, prior_order: {
                "relative_path": path,
                "source_hash": stable_hash(support_source),
                "compiled": False,
                "local_lean_stderr": "unknown identifier 'missing'",
            },
            search_formal_environment=lambda query, k: [],
        )

    checkpoint = raised.value.recovery_checkpoint
    assert raised.value.errors == ["repeated client-tool turns made no new progress"]
    assert raised.value.attempts == 3
    assert checkpoint["support_file_checks"] == 2
    assert len(
        [
            value
            for value in checkpoint["workspace_observation_fingerprints"]
            if value.startswith("lean-support-check:")
        ]
    ) == 1


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
                    {
                        "lean_source": initial,
                        "candidate_declaration_name": "target",
                    },
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
                    {
                        "lean_source": revised,
                        "candidate_declaration_name": "target",
                    },
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
                    {
                        "lean_source": revised,
                        "candidate_declaration_name": "target",
                    },
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
        LEAN_SOURCE_EDIT_TOOL,
        LEAN_SOURCE_READ_TOOL,
        LEAN_SCRATCH_TOOL,
        "search_formal_environment",
    ]
    assert backend.requests[1].tool_choice == "any"
    assert all(
        request.disable_parallel_tool_use is False
        for request in backend.requests
    )


def test_lean_candidate_workspace_keeps_stable_tools_and_linear_history() -> None:
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
                    {
                        "lean_source": authored,
                        "candidate_declaration_name": "target",
                    },
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
        LEAN_SOURCE_EDIT_TOOL,
        LEAN_SOURCE_READ_TOOL,
        LEAN_SCRATCH_TOOL,
        LEAN_SOURCE_SUBMISSION_TOOL,
        "search_formal_environment",
    }
    assert all(
        {tool.name for tool in request.tools} == expected_tools
        for request in backend.requests
    )
    assert len(backend.requests[-1].messages) == 11
    final_context = json.dumps(backend.requests[-1].messages, sort_keys=True)
    assert all(
        f"declaration query {index}" in final_context for index in range(5)
    )
    assert result.evidence["interaction_policy"] == (
        "single_model_tool_observation_budget_v1"
    )
    assert result.evidence["transcript_policy"] == CLIENT_TOOL_TRANSCRIPT_POLICY
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
                    {
                        "lean_source": failing,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-compiled",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": compiled,
                        "candidate_declaration_name": "target",
                    },
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
        max_turns=2,
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
    assert result.evidence["max_turns"] == 2
    assert result.evidence["interaction_policy"] == (
        "single_model_tool_observation_budget_v1"
    )
    assert [tool.name for tool in backend.requests[1].tools] == [
        LEAN_SOURCE_SUBMISSION_TOOL,
        LEAN_SOURCE_EDIT_TOOL,
        LEAN_SOURCE_READ_TOOL,
        LEAN_SCRATCH_TOOL,
        "search_formal_environment",
    ]
    assert backend.requests[1].tool_choice == "any"
    recovery_context = json.dumps(backend.requests[1].messages, sort_keys=True)
    assert failing in recovery_context.replace("\\n", "\n")
    assert "unknown identifier 'missing_name'" in recovery_context


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
                    {
                        "lean_source": failing,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-compiled",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": compiled,
                        "candidate_declaration_name": "target",
                    },
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
        max_no_progress_turns=2,
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
            == [
                LEAN_SOURCE_SUBMISSION_TOOL,
                LEAN_SOURCE_EDIT_TOOL,
                LEAN_SOURCE_READ_TOOL,
                LEAN_SCRATCH_TOOL,
                "search_formal_environment",
                LEAN_FORMAL_GAP_TOOL,
        ]
        for request in backend.requests[-2:]
    )
    recovery_context = json.dumps(backend.requests[-1].messages, sort_keys=True)
    assert failing in recovery_context.replace("\\n", "\n")
    assert "unknown identifier 'missing_name'" in recovery_context
    assert "client_tool_loop_terminal_decision_reason" not in (
        backend.requests[-1].metadata
    )


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
                    {
                        "lean_source": source,
                        "candidate_declaration_name": "target",
                    },
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
                    {
                        "lean_source": revised,
                        "candidate_declaration_name": "target",
                    },
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
                    {
                        "lean_source": source,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-2",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": source,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-3",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": source,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-4",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": source,
                        "candidate_declaration_name": "target",
                    },
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


def test_lean_candidate_tool_loop_does_not_recheck_an_older_candidate() -> None:
    initial = "theorem target : True := by exact missing_initial\n"
    first_revision = "theorem target : True := by exact missing_revision\n"
    accepted_revision = "theorem target : True := by exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-first",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": first_revision,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-old",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": initial,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-accepted",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": accepted_revision,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    checked_sources: list[str] = []

    def check(source, _declaration):
        checked_sources.append(source)
        return {
            "source_hash": stable_hash(source),
            "compiled": source == accepted_revision,
            "local_lean_stderr": (
                "" if source == accepted_revision else "unknown identifier"
            ),
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Repair this target.",
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
    )

    assert result.lean_source == accepted_revision
    assert checked_sources == [initial, first_revision, accepted_revision]
    assert result.evidence["source_updates"] == 2
    old = result.evidence["history"][1]["tool_calls"][0]
    assert old["is_error"] is True
    assert "previously checked" in old["result_excerpt"]


def test_semantic_revision_cannot_handoff_the_independently_rejected_source() -> None:
    rejected = "theorem target : True := by exact True.intro\n"
    failing_revision = "theorem target : True := by exact missing_name\n"
    accepted_revision = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-failing-revision",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": failing_revision,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-rejected-parent-again",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": rejected,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-changed-revision",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": accepted_revision,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    checked_sources: list[str] = []

    def check(source: str, _declaration: str):
        checked_sources.append(source)
        return {
            "source_hash": stable_hash(source),
            "compiled": source != failing_revision,
            "local_lean_stderr": (
                "unknown identifier 'missing_name'"
                if source == failing_revision
                else ""
            ),
        }

    result = run_lean_candidate_revision_tool_loop(
        provider=backend,
        system_prompt="Use tools.",
        user_prompt="Resolve the independent semantic review findings.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=4,
        max_no_progress_turns=2,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=rejected,
        check_candidate=check,
        search_formal_environment=lambda query, k: [],
        rejected_source_hash=stable_hash(rejected),
        allow_formal_gap=True,
    )

    assert result.lean_source == accepted_revision
    assert checked_sources == [
        rejected,
        failing_revision,
        accepted_revision,
    ]
    assert len(backend.requests) == 3
    repeated_parent_observation = str(backend.requests[2].messages[-1])
    assert "previously checked Lean candidate" in repeated_parent_observation
    initial_workspace = _initial_workspace(backend.requests[0])
    assert initial_workspace["revision_requirement"][
        "rejected_source_hash"
    ] == stable_hash(rejected)
    assert result.evidence["independently_rejected_source_hash"] == stable_hash(
        rejected
    )


def test_lean_candidate_tool_loop_checks_final_submission_at_turn_budget() -> None:
    initial = "theorem target : True := by exact True.intro\n"
    repaired = "theorem target : True := by\n  exact True.intro\n"
    backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-final",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": repaired,
                        "candidate_declaration_name": "target",
                    },
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
                    {
                        "lean_source": latest,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-identical-recovery",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": latest,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-identical-final-recovery",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": latest,
                        "candidate_declaration_name": "target",
                    },
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
        assert checkpoint["interaction_policy"] == (
            "single_model_tool_observation_budget_v1"
        )
        assert "final_runtime_check_performed" not in checkpoint
        assert checkpoint["model_owned_lean_code"] is True
        assert checkpoint["kernel_verified"] is False
    else:
        raise AssertionError("uncompiled final source was not checkpointed")


def test_lean_candidate_workspace_resumes_exact_state_without_parent_drift(
    tmp_path,
) -> None:
    parent = "theorem target : True := by exact missing_parent\n"
    failed = "theorem target : True := by exact missing_revision\n"
    accepted = "theorem target : True := by exact True.intro\n"
    exact_search_result = [
        {
            "qualified_declaration": "True.intro",
            "signature": "True.intro : True",
        }
    ]
    checked_sources: list[str] = []

    def check(source: str, _declaration: str) -> dict:
        checked_sources.append(source)
        return {
            "source_hash": stable_hash(source),
            "compiled": source == accepted,
            "local_lean_stderr": (
                "unknown identifier 'missing_revision'"
                if source == failed
                else "unknown identifier 'missing_parent'"
                if source == parent
                else ""
            ),
        }

    first_backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "search-1",
                    "search_formal_environment",
                    {"query": "True introduction", "max_results": 3},
                ),
                ClientToolCall(
                    "submit-failed",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": failed,
                        "candidate_declaration_name": "target",
                    },
                ),
            ),
            _response(
                ClientToolCall(
                    "submit-duplicate-recovery",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": failed,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
            _response(
                ClientToolCall(
                    "submit-duplicate-final",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": failed,
                        "candidate_declaration_name": "target",
                    },
                )
            ),
        ]
    )
    with pytest.raises(PacketValidationError) as raised:
        run_lean_candidate_revision_tool_loop(
            provider=first_backend,
            system_prompt="Use tools.",
            user_prompt="Prove the exact target.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=parent,
            check_candidate=check,
            search_formal_environment=lambda query, k: exact_search_result,
            session_dir=tmp_path / "lean-session",
        )
    checkpoint = dict(raised.value.recovery_checkpoint or {})
    assert checkpoint["resumable"] is True
    assert checkpoint["parent_source_hash"] == stable_hash(parent)
    assert checkpoint["current_source"] == failed
    assert checkpoint["last_check"]["local_lean_stderr"] == (
        "unknown identifier 'missing_revision'"
    )
    assert checkpoint["latest_formal_environment_search"]["results"] == (
        exact_search_result
    )
    assert checkpoint["checks"] == 2
    session_ref = checkpoint["client_tool_session_ref"]
    assert session_ref["artifact_kind"] == "ClientToolWorkspaceSessionRef"
    assert session_ref["authorization_fingerprint"]

    second_backend = ScriptedLeanToolBackend(
        [
            _response(
                ClientToolCall(
                    "submit-accepted",
                    LEAN_SOURCE_SUBMISSION_TOOL,
                    {
                        "lean_source": accepted,
                        "candidate_declaration_name": "target",
                    },
                )
            )
        ]
    )
    result = run_lean_candidate_revision_tool_loop(
        provider=second_backend,
        system_prompt="Use tools.",
        user_prompt="Continue the exact target.",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        model_tier="haiku",
        temperature=0.0,
        max_tokens=1200,
        max_turns=1,
        max_no_progress_turns=1,
        candidate_id="target-candidate",
        candidate_lean_declaration="target",
        initial_source=parent,
        check_candidate=check,
        search_formal_environment=lambda query, k: exact_search_result,
        recovery_checkpoint=checkpoint,
        session_dir=tmp_path / "lean-session",
    )

    resumed_state = _initial_workspace(second_backend.requests[0])
    assert "current_lean_source" not in resumed_state
    assert resumed_state["current_source_manifest"]["source_hash"] == (
        stable_hash(failed)
    )
    assert resumed_state["latest_check_observation"]["local_lean_stderr"] == (
        "unknown identifier 'missing_revision'"
    )
    assert resumed_state["latest_formal_environment_search"]["results"] == (
        exact_search_result
    )
    assert checked_sources == [parent, failed, accepted]
    assert result.evidence["parent_source_hash"] == stable_hash(parent)
    assert result.evidence["resumed_from_checkpoint_id"] == checkpoint[
        "checkpoint_id"
    ]
    assert result.evidence["local_lean_checks"] == 3
    assert result.evidence["source_updates"] == 2
    assert result.evidence["client_tool_session_lineage_continued"] is True
    assert result.evidence["resumed_from_client_tool_session_ref"] == session_ref
    window = result.evidence["client_tool_checkpoint_window"]
    assert window["policy"] == CLIENT_TOOL_RECENT_HISTORY_WINDOW_POLICY
    assert window["parent_message_count"] == session_ref["message_count"]
    assert window["checkpoint_identity"] == checkpoint["checkpoint_id"]
    assert window["prior_transcript_replayed"] is True
    assert result.evidence["transcript_policy"] == CLIENT_TOOL_TRANSCRIPT_POLICY
    assert "submit-failed" in str(second_backend.requests[0].messages)
    assert len(second_backend.requests[0].messages) >= 3


def test_lean_candidate_workspace_rejects_tampered_checkpoint_before_model_call() -> None:
    parent = "theorem target : True := by exact missing_parent\n"
    current = "theorem target : True := by exact missing_current\n"
    checkpoint = _lean_workspace_checkpoint(
        parent_source=parent,
        current_source=current,
    )
    checkpoint["last_check"]["local_lean_stderr"] = "tampered diagnostic"
    backend = ScriptedLeanToolBackend([])

    with pytest.raises(PacketValidationError) as raised:
        run_lean_candidate_revision_tool_loop(
            provider=backend,
            system_prompt="Use tools.",
            user_prompt="Continue the exact target.",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            temperature=0.0,
            max_tokens=1200,
            max_turns=1,
            max_no_progress_turns=1,
            candidate_id="target-candidate",
            candidate_lean_declaration="target",
            initial_source=parent,
            check_candidate=lambda source, declaration: {},
            search_formal_environment=lambda query, k: [],
            recovery_checkpoint=checkpoint,
        )

    assert raised.value.validation_label == "Lean workspace checkpoint lineage"
    assert backend.requests == []


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
            "overall_verdict": "REVISE",
            "candidate_id": "target-candidate",
            "semantic_review_execution_id": "semantic-execution:exact",
            "semantic_review_packet_id": "semantic-packet:exact",
            "semantic_review_packet_hash": "semantic-packet-hash",
            "findings": [
                {
                    "severity": "high",
                    "category": "mathematical_target_drift",
                    "summary": "The theorem proves only a weaker claim.",
                    "observed_behavior": (
                        "The conclusion hides the target formula."
                    ),
                    "expected_behavior": "State and prove the exact target formula.",
                    "evidence_refs": ["/exact_formal_target"],
                }
            ],
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
                    "candidate_declaration_elaborated": True,
                    "candidate_development_status": (
                        "DECLARATION_ELABORATED_PROOF_UNTRUSTED"
                    ),
                    "candidate_axiom_names": ["sorryAx"],
                    "candidate_untrusted_axiom_names": ["sorryAx"],
                    "candidate_axiom_audit_checked": True,
                    "candidate_axiom_audit_clean": False,
                }
            ],
            "formalizer_recovery_checkpoint": _lean_workspace_checkpoint(
                parent_source=initial_source,
                current_source=initial_source,
            ),
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
    assert feedback["overall_verdict"] == "REVISE"
    assert feedback["semantic_review"] == {
        "dimension_reviews": [],
        "findings": [
            {
                "severity": "high",
                "category": "mathematical_target_drift",
                "summary": "The theorem proves only a weaker claim.",
                "observed_behavior": "The conclusion hides the target formula.",
                "expected_behavior": "State and prove the exact target formula.",
                "evidence_refs": ["/exact_formal_target"],
            }
        ],
        "semantic_review_execution_id": "semantic-execution:exact",
        "semantic_review_packet_id": "semantic-packet:exact",
        "semantic_review_packet_hash": "semantic-packet-hash",
    }
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
    assert observation["candidate_declaration_elaborated"] is True
    assert observation["candidate_development_status"] == (
        "DECLARATION_ELABORATED_PROOF_UNTRUSTED"
    )
    assert observation["candidate_untrusted_axiom_names"] == ["sorryAx"]
    assert observation["candidate_axiom_audit_clean"] is False
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


def test_exhausted_formalizer_source_loop_continues_same_workspace_by_ref() -> None:
    latest = "theorem target : True := by\n  exact True.intro\n"
    checkpoint = _lean_workspace_checkpoint(
        parent_source="theorem target : True := by exact missing\n",
        current_source=latest,
    )
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
    marker = result.next_task.budget[RUNTIME_CONTINUATION_BUDGET_MARKER_KEY]
    assert marker["parent_task_id"] == "formalize:checkpoint-routing"
    assert marker["next_task_id"] == result.next_task.task_id
    routed = result.next_task.inputs["environment_feedback"]
    assert routed["artifact_kind"] == "RuntimeWorkspaceObservationRef"
    assert routed["checkpoint_id"] == checkpoint["checkpoint_id"]
    assert result.failure_classification == "formalizer_client_tool_loop_exhausted"
    failure_id = routed["source_artifact_id"]
    failure = result.produced_artifacts[failure_id]
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
    assert failure["workspace_continuation_allowed"] is True
    assert failure["workspace_continuation_errors"] == []
    assert result.evidence_entries[0].payload["architect_routing_used"] is False
    assert routed["source_artifact_hash"] == stable_hash(failure)
    assert "internal_json_regeneration_attempts" not in failure
    assert "same Formalizer" in result.rationale
    assert failure["proof_evidence_status"].endswith("NOT_PROOF_EVIDENCE")


def test_formalizer_same_owner_continuation_stops_without_new_observation() -> None:
    parent = "theorem target : True := by exact missing_parent\n"
    current = "theorem target : True := by exact missing_current\n"
    prior = _lean_workspace_checkpoint(
        parent_source=parent,
        current_source=current,
    )
    stalled_body = json.loads(json.dumps(prior))
    stalled_body.pop("checkpoint_id")
    stalled_body["resumed_from_checkpoint_id"] = prior["checkpoint_id"]
    stalled_body["segment_start_counters"] = {
        field: prior[field]
        for field in (
            "source_updates",
            "declaration_updates",
            "searches",
            "proof_searches",
            "state_inspections",
            "declaration_inspections",
            "checks",
        )
    }
    stalled_body["segment_start_observation_count"] = len(
        prior["workspace_observation_fingerprints"]
    )
    stalled_body["resumable"] = False
    stalled_body["model_owned_workspace_actions"] = False
    stalled = seal_lean_candidate_workspace_checkpoint(stalled_body)

    errors = lean_candidate_workspace_continuation_errors(
        stalled,
        prior_checkpoint=prior,
    )
    assert any("no new" in error for error in errors)
    result = runtime_module._formalizer_packet_validation_failure_result(
        task=AgentTask(
            task_id="formalizer-workspace-progress:no-progress",
            owner_subsystem="FormalizationEvaluator",
            objective="Continue only after new Lean environment evidence.",
            inputs={"formalizer_workspace_continuation_count": 1},
        ),
        question=OpenResearchQuestion(
            id="no-progress",
            title="No-progress continuation",
            description="Stop an observation-free Formalizer segment.",
        ),
        theory_packet_id="theory:no-progress",
        simulation_manifest_id="",
        algorithm_sandbox_manifest_id="",
        exc=PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool workspace",
            attempts=1,
            errors=["no new progress"],
            history=[],
            recovery_checkpoint=stalled,
        ),
        environment_feedback={"formalizer_recovery_checkpoint": prior},
    )

    assert result.status == "BLOCKED"
    assert result.next_task is None
    failure = next(
        value
        for key, value in result.produced_artifacts.items()
        if key.startswith("formalizer_validation_failure:")
    )
    assert failure["workspace_continuation_allowed"] is False
    assert any(
        "no new" in error
        for error in failure["workspace_continuation_errors"]
    )


def test_formalizer_failure_preserves_workspace_refs_without_payload_copy() -> None:
    source = "theorem target : True := by\n  exact True.intro\n"
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
    checkpoint = _lean_workspace_checkpoint(
        parent_source="older source",
        current_source=source,
        searches=1,
    )
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
    assert result.status == "REVISE"
    assert result.next_task is not None
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
    assert failure["workspace_continuation_allowed"] is False
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
    checkpoint = _lean_workspace_checkpoint(
        parent_source="theorem target : True := by exact missing\n",
        current_source="theorem target : True",
    )
    source_task = AgentTask(
        task_id="formalize:hydrate-formalizer-checkpoint",
        owner_subsystem="FormalizationEvaluator",
        objective="Author the exact Lean source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
        },
    )
    progress = runtime_module._formalizer_packet_validation_failure_result(
        task=source_task,
        question=question,
        theory_packet_id="",
        simulation_manifest_id="",
        algorithm_sandbox_manifest_id="",
        exc=PacketValidationError(
            validation_label="LLM Formalizer Lean candidate client-tool workspace",
            attempts=1,
            errors=["global client-tool turn budget exhausted"],
            history=[],
            recovery_checkpoint=checkpoint,
        ),
    )
    assert progress.status == "REVISE"
    assert progress.next_task is not None
    task = progress.next_task
    source_artifact_id = task.inputs["environment_feedback"][
        "source_artifact_id"
    ]
    stored_feedback = progress.produced_artifacts[source_artifact_id]
    blackboard = BlackboardState(
        project_id="hydrate-formalizer-checkpoint",
        artifacts=dict(progress.produced_artifacts),
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

    class SameSourceOwner:
        def propose(self, **kwargs):
            raise AssertionError("workspace continuation must not regenerate a packet")

    subsystem = runtime_module.FormalizerWorkspaceRuntimeSubsystem(
        proposal_agent=SameSourceOwner(),
    )

    result = subsystem.run(task, blackboard)

    assert result.failure_classification == "formalizer_provider_generation_failed"
    assert captured["environment_feedback"]["formalizer_recovery_checkpoint"] == (
        checkpoint
    )
    assert captured["task_environment_feedback"] == stored_feedback
    assert task.owner_subsystem == source_task.owner_subsystem
    assert task.inputs["formalizer_workspace_continuation_count"] == 1


def test_kernel_verified_formalizer_source_skips_repeat_semantic_review(
    tmp_path,
    monkeypatch,
) -> None:
    question = OpenResearchQuestion(
        id="verified-formalizer-source",
        title="Preserve a verified exact source",
        description="Do not reopen semantic review after kernel promotion.",
    )
    theory_packet_id = "theory:verified-formalizer-source"
    proposal_packet_id = "formalizer-proposal:verified-formalizer-source"
    materialization_id = "lean-candidate:verified-formalizer-source"
    source = "theorem verified_target : True := by trivial\n"
    materialization = {
        "manifest_id": materialization_id,
        "source_formalizer_packet_id": proposal_packet_id,
        "n_candidate_sources": 0,
        "n_candidate_artifacts_written": 0,
        "n_local_lean_checked": 0,
        "n_local_lean_compiled": 0,
    }
    promotion = {
        "artifact_kind": "LeanKernelPromotionResult",
        "promotion_id": "lean-kernel-promotion:verified-formalizer-source",
        "candidate_materialization_id": materialization_id,
        "candidate_id": "verified-target",
        "candidate_source_hash": stable_hash(source),
        "target_ids": ["verified-target"],
        "target_lean_declaration": "verified_target",
        "source_theorem_kernel_verified": True,
        "blockers": [],
        "proof_evidence_status": "EXACT_MODEL_SOURCE_KERNEL_VERIFIED",
    }
    monkeypatch.setattr(
        runtime_module,
        "evaluate_lean_kernel_promotion",
        lambda **_kwargs: promotion,
    )
    monkeypatch.setattr(
        runtime_module,
        "_materialize_formalizer_lean_candidate_artifacts",
        lambda **_kwargs: pytest.fail(
            "kernel-verified source was materialized a second time"
        ),
    )

    def reject_repeat_review(_materialization):
        pytest.fail("kernel-verified source was sent through semantic review again")

    monkeypatch.setattr(
        runtime_module,
        "_formalizer_compiled_exact_candidate_semantic_review_feedback",
        reject_repeat_review,
    )
    subsystem = runtime_module.FormalizerWorkspaceRuntimeSubsystem(
        lean_candidate_root=tmp_path / "candidates",
        lean_candidate_lean_project=tmp_path,
        formal_target_semantic_reviewer_available=True,
    )
    task = AgentTask(
        task_id="formalize:verified-formalizer-source",
        owner_subsystem="FormalizationEvaluator",
        objective="Promote the independently reviewed exact source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": {},
        },
    )
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts={
            theory_packet_id: {
                "artifact_kind": "TheoryDerivationPacket",
                "packet_id": theory_packet_id,
            },
            proposal_packet_id: {
                "schema_version": 1,
                "artifact_kind": "FormalizerProofEngineerProposalPacket",
                "packet_id": proposal_packet_id,
                "formal_targets": [],
                "retrieval_queries": [],
                "proof_bank_obligation_requests": [],
                "gap_taxonomy": [],
            },
            materialization_id: materialization,
        },
    )

    result = subsystem.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.failure_classification == ""
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    assert "without another source review or model rewrite" in result.rationale
    assert not any(
        row.get("artifact_kind") == "RuntimeFormalTargetSemanticReviewWorkOrder"
        for row in result.produced_artifacts.values()
        if isinstance(row, dict)
    )
    manifest = next(
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind") == "RuntimeFormalizationManifest"
    )
    assert manifest["source_theorem_kernel_verified"] is True
    assert manifest["source_theorem_kernel_verified_target_ids"] == [
        "verified-target"
    ]
    blackboard.artifacts.update(result.produced_artifacts)
    critic_result = runtime_module.CriticEvaluatorRuntimeSubsystem().run(
        result.next_task,
        blackboard,
    )
    assert critic_result.status == "ACCEPTED"
    critic_manifest = next(
        row
        for row in critic_result.produced_artifacts.values()
        if row.get("artifact_kind") == "RuntimeCriticEvaluatorManifest"
    )
    assert critic_manifest["evidence_contract_decision"][
        "source_theorem_kernel_verified"
    ] is True
    assert critic_manifest["evidence_contract_decision"][
        "final_acceptance_status"
    ] == "FORMAL_CONTRACT_SATISFIED"
    assert critic_manifest["runtime_reroute_decision"][
        "observed_conditions"
    ]["formal_proof_work_pending"] is False
    blackboard.artifacts[promotion["promotion_id"]] = {
        **blackboard.artifacts[promotion["promotion_id"]],
        "target_ids": ["different-target"],
    }
    assert runtime_module._runtime_source_theorem_kernel_closure_verified(
        formalization_manifest=manifest,
        blackboard=blackboard,
    ) is False


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
        "formalizer_recovery_checkpoint": _lean_workspace_checkpoint(
            parent_source="theorem target : True := by exact missing\n",
            current_source="theorem target : True := by trivial",
        ),
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
            workspace_source: str = source,
            inspection_symbol: str = "Example.Source",
        ) -> None:
            self.workspace_source = workspace_source
            self.inspection_symbol = inspection_symbol
            self.check_result = {}
            self.declaration_result = {}
            self.state_result = {}
            self.proof_result = {}
            self.tool_environment_identity = {}

        def run_lean_candidate_workspace_with_client_tools(self, **kwargs):
            assert kwargs["candidate_id"] == candidate_id
            assert kwargs["initial_source"] == source
            assert "reviewed_parent_source_hash" not in kwargs
            self.tool_environment_identity = dict(
                kwargs["tool_environment_identity"]
            )
            checkpoint = kwargs["environment_feedback"].get(
                "formalizer_recovery_checkpoint", {}
            )
            if self.workspace_source != source:
                assert checkpoint["current_source"] == self.workspace_source
            self.check_result = dict(
                    kwargs["check_candidate"](self.workspace_source, "target")
            )
            state_tool = kwargs.get("inspect_lean_state")
            if callable(state_tool):
                self.state_result = dict(
                    state_tool(self.workspace_source, self.check_result)
                )
            proof_tool = kwargs.get("search_proof_candidates")
            if callable(proof_tool):
                self.proof_result = dict(
                    proof_tool(
                        self.workspace_source,
                        "close the current inspected goal",
                        2,
                        {
                            **self.check_result,
                            "latest_state_inspection": self.state_result,
                            "model_lean_header": "import Mathlib\n",
                            "model_openprover_task": {
                                "context": [],
                                "target": "True",
                            },
                        },
                    )
                )
            declaration_tool = kwargs.get("inspect_lean_declaration")
            assert callable(declaration_tool)
            self.declaration_result = dict(
                    declaration_tool(
                        self.workspace_source,
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
                    "submitted_source_hash": stable_hash(self.workspace_source),
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
            self.state_calls: list[list] = []

        def inspect(self, subclaims):
            self.state_calls.append(list(subclaims))
            return [
                {
                    "residual_goals": ["|- True"],
                    "executed_tools": ["lean_lsp_mcp.lean_goal"],
                    "proof_evidence_status": (
                        "LEAN_STATE_INSPECTION_NOT_PROOF_EVIDENCE"
                    ),
                }
            ]

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

    class FakeProofSearchProvider:
        name = "fake_openprover"

        def __init__(self) -> None:
            self.requests: list[dict] = []

        def run(self, request):
            self.requests.append(dict(request))
            return {
                "status": "CANDIDATES_AVAILABLE",
                "provider": self.name,
                "source_theorem_candidate_proof_bodies": [
                    "by exact True.intro"
                ],
            }

    trace_requests: list[dict] = []

    def attach_trace_fixture(context, *, formal_source_retriever=None):
        trace_requests.append(dict(context))
        assert formal_source_retriever is None
        return {
            **dict(context),
            "proof_state_trace_rag": {
                "provider": "fixture_ai4slt_trace",
                "hits": [
                    {
                        "state_before": "|- True",
                        "tactic": "exact True.intro",
                    }
                ],
                "proof_evidence_status": (
                    "PROOF_STATE_TRACE_RETRIEVAL_CONTEXT_NOT_PROOF_EVIDENCE"
                ),
            },
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
            "candidate_declaration_elaborated": True,
            "candidate_development_status": (
                "DECLARATION_ELABORATED_PROOF_VERIFIED"
            ),
            "candidate_axiom_names": ["Classical.choice"],
            "candidate_untrusted_axiom_names": [],
            "candidate_axiom_audit_checked": True,
            "candidate_axiom_audit_clean": True,
        },
    )
    monkeypatch.setattr(
        runtime_module,
        "attach_ai4slt_proof_state_trace_rag",
        attach_trace_fixture,
    )
    monkeypatch.setattr(
        runtime_module,
        "proof_state_feedback_row_to_json",
        lambda row: dict(row),
    )
    agent = FakeAgent()
    proof_state_provider = FakeProofStateProvider()
    proof_search_provider = FakeProofSearchProvider()
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
        proof_search_provider=proof_search_provider,
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
    assert agent.check_result["candidate_declaration_elaborated"] is True
    assert agent.check_result["candidate_development_status"] == (
        "DECLARATION_ELABORATED_PROOF_VERIFIED"
    )
    assert agent.check_result["candidate_axiom_names"] == [
        "Classical.choice"
    ]
    assert agent.check_result["candidate_axiom_audit_clean"] is True
    assert evidence["parent_candidate_source_hash"] == stable_hash(source)
    assert evidence["resumed_from_model_checkpoint"] is False
    proof_request = proof_search_provider.requests[0]
    assert proof_request["current_lean_source_hash"] == stable_hash(source)
    assert proof_request["proof_state_observation"] == agent.state_result
    assert proof_request["proof_state_observation_hash"] == stable_hash(
        agent.state_result
    )
    assert proof_request["residual_goal_excerpt"] == ["|- True"]
    assert proof_request["lean_header"] == "import Mathlib\n"
    assert proof_request["openprover_task"] == {
        "context": [],
        "target": "True",
    }
    assert len(trace_requests) == 1
    assert trace_requests[0]["model_query"] == (
        "close the current inspected goal"
    )
    assert trace_requests[0]["proof_state_observation"] == agent.state_result
    assert proof_request["proof_state_trace_rag"]["provider"] == (
        "fixture_ai4slt_trace"
    )
    assert proof_request["request_fingerprint"] == stable_hash(
        {
            key: value
            for key, value in proof_request.items()
            if key != "request_fingerprint"
        }
    )
    assert agent.proof_result["source_theorem_candidate_proof_bodies"] == [
        "by exact True.intro"
    ]
    assert agent.state_result["source_hash"] == stable_hash(source)
    assert proof_state_provider.state_calls
    assert agent.declaration_result["status"] == "OBSERVED"
    assert proof_state_provider.calls[0]["symbol"] == "Example.Source"
    assert agent.tool_environment_identity["lean_project"] == str(
        tmp_path.resolve()
    )
    assert agent.tool_environment_identity["formal_source_retriever"] == {
        "configured": False
    }
    assert agent.tool_environment_identity["proof_state_provider"]["name"] == (
        "fake_lean_lsp_mcp"
    )
    inspected_path = proof_state_provider.calls[0]["artifact_path"]
    assert stable_hash(
        Path(inspected_path).read_text(encoding="utf-8")
    ) == stable_hash(source)
    indexed_source_path = tmp_path / "IndexedSource.lean"
    indexed_source_path.write_text(
        "import Mathlib\n\nnamespace Example.Namespace\n\n"
        "open MeasureTheory\n\nstructure Source where\n  value : Nat\n\n"
        "end Example.Namespace\n",
        encoding="utf-8",
    )

    class IndexedDeclaration:
        name = "Example.Namespace.Source"
        namespace = "Example.Namespace"
        path = str(indexed_source_path)
        line = 7
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
    assert indexed_agent.declaration_result["indexed_declaration_line"] == 7
    assert indexed_agent.declaration_result["indexed_declaration_signature"] == (
        "structure Source where"
    )
    assert indexed_agent.declaration_result[
        "indexed_symbol_context_observed"
    ] is True
    api_context = indexed_agent.declaration_result[
        "active_project_api_context"
    ]
    assert api_context["importable_module"] == "IndexedSource"
    assert api_context["qualified_declaration"] == "Example.Namespace.Source"
    assert api_context["namespace_path"] == "Example.Namespace"
    assert api_context["exact_signature"] == "structure Source where"
    assert "structure Source where" in api_context[
        "declaration_source_context"
    ]["content"]
    module_prefix = api_context["source_module_prefix_reference"]
    assert module_prefix["start_line"] == 1
    assert "import Mathlib" in module_prefix["content"]
    assert "namespace Example.Namespace" in module_prefix["content"]
    assert "open MeasureTheory" in module_prefix["content"]
    assert "indexed_source_context" not in indexed_agent.declaration_result
    assert "indexed_module_prefix_context" not in (
        indexed_agent.declaration_result
    )

    resumed_source = "theorem target : True := by\n  exact True.intro\n"
    resume_checkpoint = _lean_workspace_checkpoint(
        parent_source=source,
        current_source=resumed_source,
        candidate_id=candidate_id,
    )
    resume_checkpoint.update(
        {
            "parent_formalizer_artifact_id": parent_packet_id,
            "parent_formalizer_packet_id": parent_packet_id,
        }
    )
    resume_checkpoint = seal_lean_candidate_workspace_checkpoint(
        resume_checkpoint
    )
    resume_feedback = {
        **feedback,
        "formalizer_recovery_checkpoint": resume_checkpoint,
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


def test_formalizer_materialization_preserves_exact_workspace_source_hash(
    tmp_path,
) -> None:
    source = "theorem target : True := by exact True.intro\n\n"
    question = OpenResearchQuestion(
        id="exact-source-identity",
        title="Exact source identity",
        description="Preserve model-authored Lean bytes through materialization.",
    )
    task = AgentTask(
        task_id="formalize:exact-source-identity:1",
        owner_subsystem="FormalizationEvaluator",
        objective="Materialize the exact model source.",
    )
    proposal_packet = {
        "packet_id": "formalizer_proposal:exact-source-identity",
        "formal_targets": [
            {
                "id": "target-candidate",
                "formal_target_role": (
                    FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE
                ),
                "candidate_lean_declaration": "target",
                "lean_statement_sketch": source,
                "lean_imports": [],
                "expected_status": "NEEDS_KERNEL_CHECK",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "target",
                },
            }
        ],
    }

    materialization = (
        runtime_module._materialize_formalizer_lean_candidate_artifacts(
            root=tmp_path,
            question=question,
            task=task,
            proposal_packet=proposal_packet,
        )
    )

    row = materialization["candidate_rows"][0]
    assert row["source_hash"] == stable_hash(source)
    assert Path(row["artifact_path"]).read_text(encoding="utf-8") == source


def test_formalizer_materialization_preserves_exact_multifile_project(
    tmp_path,
) -> None:
    source = "import AIStat.Support\n\ntheorem target : True := by exact AIStat.helper\n"
    support_path = "AIStat/Support.lean"
    support_source = "namespace AIStat\ntheorem helper : True := by trivial\nend AIStat\n"
    project = model_authored_lean_project(
        target_source=source,
        project_files=[{"path": support_path, "content": support_source}],
        support_build_order=(support_path,),
    )
    project_ref = persist_model_authored_lean_project(
        project,
        target_source=source,
        root=tmp_path / "formalizer-owner",
    )
    question = OpenResearchQuestion(
        id="exact-project-identity",
        title="Exact project identity",
        description="Preserve model-authored Lean project bytes.",
    )
    task = AgentTask(
        task_id="formalize:exact-project-identity:1",
        owner_subsystem="FormalizationEvaluator",
        objective="Materialize the exact model project.",
    )
    proposal_packet = {
        "packet_id": "formalizer_proposal:exact-project-identity",
        "formal_targets": [
            {
                "id": "target-candidate",
                "formal_target_role": FORMAL_TARGET_ROLE_SOURCE_THEOREM_CANDIDATE,
                "candidate_lean_declaration": "target",
                "lean_statement_sketch": source,
                "lean_project": project_ref,
                "expected_status": "NEEDS_KERNEL_CHECK",
                "source_theorem_target_provenance": {
                    "source_theorem_target_known": True,
                    "target_lean_declaration": "target",
                },
            }
        ],
    }

    materialization = runtime_module._materialize_formalizer_lean_candidate_artifacts(
        root=tmp_path,
        question=question,
        task=task,
        proposal_packet=proposal_packet,
    )

    row = materialization["candidate_rows"][0]
    assert row["lean_project"] == project_ref
    assert row["lean_project_hash"] == project["project_hash"]
    target_path = Path(row["artifact_path"])
    assert target_path.name == "Main.lean"
    assert target_path.read_text(encoding="utf-8") == source
    assert (target_path.parent / support_path).read_text(encoding="utf-8") == (
        support_source
    )


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
    harness_events = []

    class FormalSourceRetriever:
        def __init__(self) -> None:
            self.calls = []

        def search(self, query, *, k):
            self.calls.append({"query": query, "k": k})
            harness_events.append({"event": "retrieval", "query": query})

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

        def generate_client_tool_turn(self, request):
            harness_events.append({"event": "model_turn"})
            return super().generate_client_tool_turn(request)

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
            client_tool_lean_candidate_max_turns=4,
            client_tool_lean_candidate_max_no_progress_turns=1,
        ),
    )
    proof_state_provider = ProofStateProvider()
    formal_source_retriever = FormalSourceRetriever()
    subsystem = runtime_module.FormalizerWorkspaceRuntimeSubsystem(
        proposal_agent=agent,
        proof_state_provider=proof_state_provider,
        formal_source_retriever=formal_source_retriever,
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
    assert harness_events[0] == {"event": "model_turn"}
    assert formal_source_retriever.calls == [
        {"query": "Project.Source", "k": 8},
        {"query": "Project.Source", "k": 8},
    ]
    initial_messages = json.dumps(backend.requests[0].messages, sort_keys=True)
    assert "indexed_lean_environment_candidates" not in initial_messages
    assert "retrieval_query_seeds" not in initial_messages
    assert "at most 4 model-tool turns" not in backend.requests[0].system_prompt
    assert "The same tools remain available" in backend.requests[0].system_prompt
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
    materializations = [
        row
        for row in result.produced_artifacts.values()
        if row.get("artifact_kind")
        == "RuntimeFormalizerLeanCandidateMaterialization"
    ]
    assert len(materializations) == 1
    materialized_row = materializations[0]["candidate_rows"][0]
    assert materialized_row["source_hash"] == workspaces[0][
        "submitted_source_hash"
    ]
    assert Path(materialized_row["artifact_path"]).read_text(
        encoding="utf-8"
    ) == authored
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
        "formal_source_scope_ids": ["statlib"],
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
    attempted_source = "theorem exact_target : True := by sorry\n"
    workspace = {
        "schema_version": 1,
        "artifact_kind": "LeanCandidateClientToolWorkspace",
        "disposition": "FORMAL_GAP",
        "candidate_id": "exact-target",
        "submitted_source_hash": stable_hash(attempted_source),
        "workspace_phase": "initial_authoring",
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
        "formal_gap_observation": {
            "formal_gap": formal_gap,
            "candidate_id": "exact-target",
            "candidate_lean_declaration": "exact_target",
            "current_source": attempted_source,
            "current_source_hash": stable_hash(attempted_source),
            "parent_source_hash": stable_hash(""),
            "latest_check_observation": {
                "source_hash": stable_hash(attempted_source),
                "compiled": False,
                "local_lean_source_compiled": True,
                "local_lean_stderr": "declaration uses sorryAx",
            },
            "latest_formal_environment_search": {},
            "latest_proof_search": {},
            "latest_state_inspection": {},
            "latest_declaration_inspection": {},
            "model_owned_lean_code": True,
            "runtime_selected_lean_code": False,
            "kernel_verified": False,
            "proof_evidence_status": (
                "MODEL_REPORTED_FORMAL_GAP_OBSERVATION_NOT_PROOF_EVIDENCE"
            ),
        },
    }

    monkeypatch.setattr(
        runtime_module,
        "_runtime_formalizer_client_tool_workspace_available",
        lambda **_kwargs: True,
    )
    workspace_call = {}

    def fake_workspace(**kwargs):
        workspace_call.update(kwargs)
        return proposal, workspace

    monkeypatch.setattr(
        runtime_module,
        "_runtime_formalizer_lean_candidate_client_tool_workspace",
        fake_workspace,
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
    assert workspace_call["formal_source_scope_ids"] == ("statlib",)
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
                    {
                        "lean_source": repaired,
                        "candidate_declaration_name": "target",
                    },
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
        "overall_verdict": "REVISE",
        "candidate_source_hash": stable_hash(original),
        "formalizer_workspace_context": {
            "formalizer_candidate_semantic_review_status": (
                "INDEPENDENT_SEMANTIC_REVIEW_REVISE_NOT_PROOF_EVIDENCE"
            ),
            "formalizer_candidate_semantic_review_candidate_source_hash": (
                stable_hash(original)
            ),
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
    initial_workspace = _initial_workspace(backend.requests[0])
    assert initial_workspace["revision_requirement"][
        "rejected_source_hash"
    ] == stable_hash(original)
    assert backend.requests[0].metadata["client_tool_loop_max_turns"] == (
        FormalizerConfig().client_tool_lean_candidate_max_turns
    )
    assert FormalizerConfig().client_tool_lean_candidate_max_turns == 48
    assert "up to 48 model/tool turns" in str(backend.requests[0].messages)

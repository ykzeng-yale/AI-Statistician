"""Production bindings and real execution, not model or mathematical efficacy."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import replace

import pytest

from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from ai_statistician.client_tool_loop import run_client_tool_workspace
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import ClientToolCall, ClientToolTurnRequest, ClientToolTurnResponse
from ai_statistician.research_agent_runtime import _run_generated_code_sandbox
from ai_statistician.research_architect import LLMTheoryDeveloperAgent, ResearchArchitectConfig, validate_theory_packet
from ai_statistician.research_control import prepare_research_control_workspace
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_SOURCE_COMMIT_TOOL, SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
)
from ai_statistician.scientific_sandbox import discover_scientific_sandbox_runtime
from ai_statistician.simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_COMMIT_TOOL, THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL, THEORY_WORKSPACE_WRITE_TOOL,
    load_theory_workspace_documents,
)


MODEL = "Qwen3-4B-Instruct-2507"


class Scripted:
    provider_name = "local"

    def __init__(self, calls):
        self.calls = list(calls)
        self.requests = []

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        item = self.calls.pop(0)
        call = item(request) if callable(item) else item
        return ClientToolTurnResponse(
            content_blocks=({"type": "tool_use", "id": call.call_id, "name": call.name, "input": dict(call.input)},),
            tool_calls=(call,), text="", provider="local", model=MODEL,
            metadata={"tools_executed_by_backend": False},
        )


@pytest.mark.parametrize("driver", ["direct", "prepared", "shared"])
def test_actual_theory_binding_keeps_its_validator_and_document_authority(tmp_path, monkeypatch, driver):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    question = OpenResearchQuestion("opaque", "Opaque transport", "This is not a statistical theorem.",
                                    task_intent={"theory": "required", "scientific_code": "not_applicable",
                                                 "empirical": "not_applicable", "formal": "not_applicable"})
    document = "# Opaque record\n\n## opaque_claim\n\nUnresolved placeholder, not an established result.\n"
    handoffs = {
        "problem_card": {"claim_ids": ["opaque_claim"]},
        "theory_derivation_packet": {"claim_index": [{
            "id": "opaque_claim", "kind": "definition", "document_path": "claim.md",
            "anchor": "opaque_claim", "depends_on": [], "status": "OPEN",
        }]},
    }
    calls = [
        ClientToolCall("document", THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL, {"path": "claim.md", "content": document}),
        ClientToolCall("bad-index", THEORY_WORKSPACE_WRITE_TOOL,
                       {"writes": [{"artifact_name": "problem_card", "value": {"claim_ids": ["missing"]}}]}),
        ClientToolCall("index", THEORY_WORKSPACE_WRITE_TOOL,
                       {"writes": [{"artifact_name": name, "value": value} for name, value in handoffs.items()]}),
        ClientToolCall("commit", THEORY_WORKSPACE_COMMIT_TOOL, {"readiness_rationale": "Checkpoint for review only."}),
    ]
    backend = Scripted(calls)
    developer = LLMTheoryDeveloperAgent(provider=backend, config=ResearchArchitectConfig(
        provider_name="local", model=MODEL, model_tier="local", serious_model=MODEL, serious_model_tier="local",
        max_tokens=1024, temperature=0, theory_workspace_max_turns=8, theory_workspace_max_tool_calls=8,
    ))
    if driver == "direct":
        packet = developer.derive(question, theory_workspace_root=tmp_path / "theory")
    else:
        prepared = developer.prepare_workspace(question, theory_workspace_root=tmp_path / "theory")
        assert not backend.requests
        if driver == "prepared":
            question.task_intent["formal"] = "required"  # Caller edits cannot change a prepared contract.
            packet = run_client_tool_workspace(backend=backend, workspace=prepared)
        else:
            captured = {}

            def binding(scope, payload):
                captured.update(packet=deepcopy(payload["core_packet"]), hash=stable_hash(payload))
                return {"resources": {path: hashlib.sha256(body.encode()).hexdigest()
                                      for path, body in load_theory_workspace_documents(payload).items()}, "inputs": {}}

            backend.calls = [replace(call, name="theory__" + call.name) for call in calls]
            backend.calls.append(lambda request: ClientToolCall("report", "submit_research_result", {
                "report_markdown": "# Honest unresolved submission\n",
                "selected_checkpoints": {"theory": captured["hash"]},
            }))
            control = prepare_research_control_workspace(
                question=question, request=ClientToolTurnRequest(system_prompt="Common objective.", messages=(), tools=(),
                                                               model=MODEL, max_tokens=1024),
                workspaces={"theory": prepared}, checkpoint_bindings=binding, session_dir=tmp_path / "joint",
                session_id="actual-binding", max_turns=8, max_tool_calls=8, max_no_progress_turns=8,
            )
            result = run_client_tool_workspace(backend=backend, workspace=control)
            packet = captured["packet"]
            assert result.terminal_payload["independent_role_review"] is False
            assert "llm_client_tool_loop" not in packet  # No isolated-owner receipt.
    assert validate_theory_packet(packet) == []
    assert load_theory_workspace_documents(packet) == {"claim.md": document}
    assert packet["theory_derivation_packet"]["claim_index"][0]["status"] == "OPEN"
    assert "claim_index must be non-empty" in str(backend.requests[2].messages)
    assert len(backend.requests) == (5 if driver == "shared" else 4)


@pytest.mark.parametrize("role", ["algorithm", "simulation"])
@pytest.mark.parametrize("language", ["python", "r"])
@pytest.mark.parametrize("driver", ["direct", "prepared", "shared"])
def test_actual_scientific_agent_uses_the_production_executor_unchanged(tmp_path, monkeypatch, role, language, driver):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    runtime = discover_scientific_sandbox_runtime()
    if not (runtime.python_available if language == "python" else runtime.r_available):
        pytest.skip("scientific runtime is not prepared")
    draft = {"language": language, "execution_profile": "scientific_wasm", "dependencies": [],
             "entrypoint": "run_sandbox", "code": (
                 "def run_sandbox(seed, replicates):\n    return {'opaque': seed + replicates}\n"
                 if language == "python" else
                 "run_sandbox <- function(seed, replicates) list(opaque=seed+replicates)\n")}
    calls = [ClientToolCall("source", SCIENTIFIC_SOURCE_SUBMISSION_TOOL, draft),
             ClientToolCall("execute", SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, {"reason": "Inspect the exact source."}),
             ClientToolCall("commit", SCIENTIFIC_SOURCE_COMMIT_TOOL, {})]
    backend = Scripted(calls)
    agent_class, config_class = ((LLMAlgorithmEngineerAgent, AlgorithmEngineerConfig) if role == "algorithm"
                                 else (LLMSimulationEngineerAgent, SimulationEngineerConfig))
    agent = agent_class(provider=backend, config=config_class(provider_name="local", model=MODEL, model_tier="local",
                                                            max_tokens=1024, temperature=0, client_tool_code_max_turns=8))
    executions = []

    def check(candidate):
        row, record = _run_generated_code_sandbox(
            sandbox_dir=tmp_path / "execution", estimator_id="opaque", spec={"id": "opaque"},
            code_draft=candidate, n_runs=3, seed=7, timeout_s=30,
        )
        executions.append((row, record))
        return {"code_draft_hash": stable_hash(candidate), "accepted": row["smoke_passed"], "prototype": row}

    body = "# Exact upstream context\n\nOpaque input, not a mathematical conclusion.\n"
    context = {"theory_context": {"document_authoritative": True, "authoritative_theory_documents": [{
        "path": "claim.md", "content": body, "sha256": hashlib.sha256(body.encode()).hexdigest(),
    }]}}
    options = dict(question=OpenResearchQuestion("opaque", "Opaque source", "No scientific inference requested."),
                   artifact_id="opaque", code_draft=None, initial_observation={}, workspace_context=context,
                   check_candidate=check, workspace_operation="initial_authoring", session_dir=tmp_path / "source")
    if driver == "direct":
        result = agent.iterate_code_with_tools(**options)
        assert result.code_draft == draft and result.evidence["model_owned_source"] is True
    else:
        prepared = agent.prepare_code_workspace(**options)
        assert not backend.requests and not executions
        assert prepared.initial_context["read_only_documents"][0]["sha256"] == hashlib.sha256(body.encode()).hexdigest()
        if driver == "prepared":
            result = run_client_tool_workspace(backend=backend, workspace=prepared)
            assert result.code_draft == draft and result.evidence["model_owned_source"] is True
        else:
            refs = {}

            def binding(scope, payload):
                refs[scope] = stable_hash(payload)
                return {"resources": {"project": payload["check_result"]["prototype"]["project_hash"]}, "inputs": {}}

            backend.calls = [replace(call, name="source__" + call.name) for call in calls]
            backend.calls.append(lambda request: ClientToolCall("report", "submit_research_result", {
                "report_markdown": "# Execution only\n", "selected_checkpoints": refs,
            }))
            control = prepare_research_control_workspace(
                question=options["question"], request=ClientToolTurnRequest(system_prompt="Common objective.", messages=(),
                                                                          tools=(), model=MODEL, max_tokens=1024),
                workspaces={"source": prepared}, checkpoint_bindings=binding, session_dir=tmp_path / "joint",
                session_id="actual-source", max_turns=8, max_tool_calls=8, max_no_progress_turns=8,
            )
            result = run_client_tool_workspace(backend=backend, workspace=control)
            assert result.terminal_payload["independent_role_review"] is False
    assert len(executions) == 1
    row, record = executions[0]
    assert row["source_code"] == draft["code"] and row["script_hash"] == stable_hash(draft["code"])
    assert row["metrics"] == {"opaque": 10}
    assert row["execution_smoke_passed"] is True and row["promotion_ready"] is False
    assert record.exit_status == "0"

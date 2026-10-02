"""Production bindings and real execution, not model or mathematical efficacy."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace

import pytest

from ai_statistician.algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from ai_statistician.agent_runtime import AgentRuntime, AgentTask, BlackboardState, load_persisted_runtime_result
from ai_statistician.architect_metric_semantic_reviewer_llm import (
    ArchitectMetricSemanticReviewerConfig, LLMArchitectMetricSemanticReviewerAgent,
)
from ai_statistician.architect_theory_execution_preflight import (
    ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL, PREFLIGHT_EXECUTION_HANDOFF_NOT_REQUIRED,
    prepare_architect_theory_execution_preflight_workspace,
)
from ai_statistician.client_tool_loop import run_client_tool_workspace
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import ClientToolCall, ClientToolTurnRequest, ClientToolTurnResponse
from ai_statistician.metric_protocol_stage import build_theory_informed_metric_protocol_material
from ai_statistician.research_agent_runtime import (
    CriticEvaluatorRuntimeSubsystem, _persist_runtime_artifact_store, _run_generated_code_sandbox,
)
from ai_statistician.research_architect import LLMTheoryDeveloperAgent, ResearchArchitectConfig, validate_theory_packet
from ai_statistician.research_control import (
    RESEARCH_CONTROL_INPUTS_TOOL, load_research_control_submission,
    prepare_research_control_workspace, prepare_single_context_research_workspace,
)
from ai_statistician.research_gold_evaluation import _hidden_execution_summary, _run_hidden_scientific_harness
from ai_statistician.research_evaluation import load_runtime_research_submission
from ai_statistician.research_schema import OpenResearchQuestion, research_question_payload
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_SOURCE_COMMIT_TOOL, SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, SCIENTIFIC_SOURCE_SUBMISSION_TOOL,
)
from ai_statistician.scientific_sandbox import ScientificEstimatorBinding, discover_scientific_sandbox_runtime
from ai_statistician.simulation_engineer_llm import LLMSimulationEngineerAgent, SimulationEngineerConfig
from ai_statistician.theory_derivation_trace import document_authoritative_theory_context
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_COMMIT_TOOL, THEORY_WORKSPACE_READ_DOCUMENT_TOOL, THEORY_SCRATCHPAD_TOOL,
    THEORY_WORKSPACE_GAP_TOOL, THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL, THEORY_WORKSPACE_WRITE_TOOL,
    load_theory_workspace_documents, theory_workspace_document_manifest,
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


@pytest.mark.parametrize("role", ["algorithm", "simulation"])
@pytest.mark.parametrize("language", ["python", "r"])
def test_selected_upstream_context_reaches_the_actual_owner_before_source_authoring(tmp_path, monkeypatch, role, language):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    runtime = discover_scientific_sandbox_runtime()
    if not (runtime.python_available if language == "python" else runtime.r_available):
        pytest.skip("scientific runtime is not prepared")
    question = OpenResearchQuestion("opaque-inputs", "Opaque contexts", "Unresolved transport task.",
                                    task_intent={"theory": "required", "scientific_code": "not_applicable",
                                                 "empirical": "not_applicable", "formal": "not_applicable"})
    backend = Scripted([])
    theory = LLMTheoryDeveloperAgent(provider=backend, config=ResearchArchitectConfig(
        provider_name="local", model=MODEL, model_tier="local", serious_model=MODEL, serious_model_tier="local",
        max_tokens=1024, temperature=0,
    )).prepare_workspace(question, theory_workspace_root=tmp_path / "theory")
    agent_class, config_class = ((LLMAlgorithmEngineerAgent, AlgorithmEngineerConfig) if role == "algorithm"
                                 else (LLMSimulationEngineerAgent, SimulationEngineerConfig))
    agent = agent_class(provider=backend, config=config_class(provider_name="local", model=MODEL, model_tier="local",
                                                            max_tokens=1024, temperature=0))
    checkpoints, executions, prepared_contexts = {}, [], []

    def prepare_source(selected, previous):
        inputs = {scope: {"payload_hash": row["reference"]["payload_hash"],
                          "resources": deepcopy(row["reference"]["resources"])}
                  for scope, row in selected.items()}
        core = selected["theory"]["payload"]["core_packet"] if selected else {}
        context = {"theory_context": document_authoritative_theory_context(core),
                   "estimator_spec": {"id": "opaque", "request_key": "opaque-input"}}

        def execute(candidate):
            row, record = _run_generated_code_sandbox(
                sandbox_dir=tmp_path / "execution", estimator_id="opaque", spec=context["estimator_spec"],
                code_draft=candidate, validation_context={"bound_workspace_context": context},
                n_runs=3, seed=7, timeout_s=30,
            )
            executions.append((row, record, deepcopy(inputs)))
            return {"code_draft_hash": stable_hash(candidate), "accepted": row["smoke_passed"],
                    "prototype": row, "checkpoint_inputs": deepcopy(inputs)}

        prepared = agent.prepare_code_workspace(
            question=question, artifact_id="opaque", code_draft=previous["code_draft"] if previous else None,
            initial_observation={}, workspace_context=context, check_candidate=execute,
            workspace_operation="targeted_revision" if previous else "initial_authoring",
            allow_current_source_run=True, session_dir=tmp_path / "source",
        )
        prepared_contexts.append(prepared.initial_context)
        return prepared

    def bindings(scope, payload):
        checkpoints.setdefault(scope, []).append(stable_hash(payload))
        if scope == "theory":
            docs = load_theory_workspace_documents(payload)
            return {"resources": {path: hashlib.sha256(body.encode()).hexdigest() for path, body in docs.items()},
                    "inputs": {}}
        return {"resources": {"project": payload["check_result"]["prototype"]["project_hash"]},
                "inputs": payload["check_result"]["checkpoint_inputs"]}

    joint = prepare_research_control_workspace(
        question=question, request=ClientToolTurnRequest(system_prompt="Common objective.", messages=(), tools=(),
                                                       model=MODEL, max_tokens=1024),
        workspaces={"theory": theory, "source": prepare_source({}, None)},
        input_workspace_preparers={"source": prepare_source}, checkpoint_bindings=bindings,
        session_dir=tmp_path / "joint", session_id="selected-inputs", max_turns=30, max_tool_calls=30,
        max_no_progress_turns=30,
    )
    handoffs = {"problem_card": {"claim_ids": ["opaque_claim"]},
                "theory_derivation_packet": {"claim_index": [{"id": "opaque_claim", "kind": "definition",
                    "document_path": "claim.md", "anchor": "opaque_claim", "depends_on": [], "status": "OPEN"}]}}
    first = "# Opaque record\n\n## opaque_claim\n\nFirst unresolved input.\n"
    second = "# Opaque record\n\n## opaque_claim\n\nDifferent unresolved input.\n"
    draft = {"language": language, "execution_profile": "scientific_wasm", "dependencies": [],
             "entrypoint": "run_sandbox", "code": ("def run_sandbox(seed, replicates):\n    return {'opaque': 10}\n"
                if language == "python" else "run_sandbox <- function(seed, replicates) list(opaque=10)\n")}

    def select(index):
        return ClientToolCall("select-" + str(index), RESEARCH_CONTROL_INPUTS_TOOL,
                             {"scope": "source", "selected_checkpoints": {"theory": checkpoints["theory"][index]}})

    def submit(source_index):
        return ClientToolCall("report-" + str(source_index), "submit_research_result", {
            "report_markdown": "# Transport only, not scientific acceptance\n",
            "selected_checkpoints": {"theory": checkpoints["theory"][1], "source": checkpoints["source"][source_index]},
        })

    read = {"path": "claim.md", "line_start": 1, "line_end": 5}
    backend.calls = [
        ClientToolCall("unbound", "source__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL, draft),
        ClientToolCall("first", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL, {"path": "claim.md", "content": first}),
        ClientToolCall("index", "theory__" + THEORY_WORKSPACE_WRITE_TOOL,
                       {"writes": [{"artifact_name": name, "value": value} for name, value in handoffs.items()]}),
        ClientToolCall("checkpoint-one", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL, {"readiness_rationale": "Unresolved first checkpoint."}),
        ClientToolCall("second", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL, {"path": "claim.md", "content": second}),
        ClientToolCall("checkpoint-two", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL, {"readiness_rationale": "Unresolved second checkpoint."}),
        lambda request: select(0),
        ClientToolCall("read-one", "source__" + THEORY_WORKSPACE_READ_DOCUMENT_TOOL, read),
        ClientToolCall("source", "source__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL, draft),
        ClientToolCall("execute-one", "source__" + SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, {"reason": "Check exact source."}),
        ClientToolCall("commit-one", "source__" + SCIENTIFIC_SOURCE_COMMIT_TOOL, {}),
        lambda request: replace(select(0), call_id="select-same"),  # No new preparer or erased execution state.
        lambda request: submit(0),  # Later Theory is not the context supplied to this source checkpoint.
        lambda request: select(1),
        ClientToolCall("read-two", "source__" + THEORY_WORKSPACE_READ_DOCUMENT_TOOL, read),
        ClientToolCall("execute-two", "source__" + SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, {"reason": "Check retained source under the selected new context."}),
        ClientToolCall("commit-two", "source__" + SCIENTIFIC_SOURCE_COMMIT_TOOL, {}),
        lambda request: submit(1),
    ]
    result = run_client_tool_workspace(backend=backend, workspace=joint)
    assert len(executions) == 2 and len(prepared_contexts) == 3
    assert executions[0][0]["source_code"] == executions[1][0]["source_code"] == draft["code"]
    assert all(row["metrics"] == {"opaque": 10} and record.exit_status == "0" for row, record, _ in executions)
    assert "exact inputs before using its actions" in str(backend.requests[1].messages)
    assert "First unresolved input." in str(backend.requests[8].messages[-1])
    assert "Different unresolved input." in str(backend.requests[15].messages[-1])
    assert "selected checkpoint inputs do not match" in str(backend.requests[13].messages[-1])
    assert prepared_contexts[1]["workspace_context"]["estimator_spec"]["request_key"] == "opaque-input"
    assert prepared_contexts[1]["read_only_documents"][0]["sha256"] == hashlib.sha256(first.encode()).hexdigest()
    assert prepared_contexts[2]["read_only_documents"][0]["sha256"] == hashlib.sha256(second.encode()).hexdigest()
    selection = result.terminal_payload["selected_checkpoints"]
    assert selection["source"]["provided_inputs"]["theory"]["payload_hash"] == checkpoints["theory"][1]
    assert selection["source"]["inputs"] == executions[1][2]
    assert result.terminal_payload["independent_role_review"] is False


@pytest.mark.parametrize("language", ["python", "r"])
@pytest.mark.parametrize("offset", [0, 1])
@pytest.mark.parametrize("include_review", [False, True])
def test_application_control_runs_actual_theory_estimator_and_simulation(tmp_path, monkeypatch, language, offset, include_review):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    runtime = discover_scientific_sandbox_runtime()
    if not (runtime.python_available if language == "python" else runtime.r_available):
        pytest.skip("scientific runtime is not prepared")
    question = OpenResearchQuestion("opaque-application", "Opaque application", "Mechanism test, not scientific acceptance.",
                                    task_intent={"theory": "optional", "scientific_code": "not_applicable",
                                                 "empirical": "not_applicable", "formal": "not_applicable"})
    backend = Scripted([])
    theory = LLMTheoryDeveloperAgent(provider=backend, config=ResearchArchitectConfig(
        provider_name="local", model=MODEL, model_tier="local", serious_model=MODEL, serious_model_tier="local",
        max_tokens=1024, temperature=0,
    ))
    algorithm = LLMAlgorithmEngineerAgent(provider=backend, config=AlgorithmEngineerConfig(
        provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0,
    ))
    simulation = LLMSimulationEngineerAgent(provider=backend, config=SimulationEngineerConfig(
        provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0,
    ))
    workspace = prepare_single_context_research_workspace(
        question=question, request=ClientToolTurnRequest(system_prompt="Common research objective.", messages=(), tools=(),
                                                       model=MODEL, max_tokens=1024),
        theory_agent=theory, algorithm_agent=algorithm, simulation_agent=simulation, estimator_id="opaque",
        session_dir=tmp_path, session_id="opaque-app", n_runs=3, seed=7, timeout_s=30,
        max_turns=24, max_tool_calls=24, max_no_progress_turns=24,
        theory_reviewer=LLMArchitectMetricSemanticReviewerAgent(provider=backend, config=ArchitectMetricSemanticReviewerConfig(
            provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0,
        )) if include_review else None,
    )
    assert not backend.requests
    refs = {}
    first_theory = {}

    def references(request):
        for message in request.messages:
            if message.get("role") != "user" or not isinstance(message.get("content"), list):
                continue
            for block in message["content"]:
                if block.get("type") != "tool_result" or not isinstance(block.get("content"), list):
                    continue
                for part in block["content"]:
                    item = json.loads(part["text"])
                    if "shared_checkpoint_ref" in item:
                        ref = item["shared_checkpoint_ref"]
                        refs[ref["scope"]] = ref["payload_hash"]
        return refs

    def select(request, scope, parents):
        observed = references(request)
        first_theory.setdefault("hash", observed["theory"])
        return ClientToolCall("select-" + scope, RESEARCH_CONTROL_INPUTS_TOOL,
                             {"scope": scope, "selected_checkpoints": {parent: observed[parent] for parent in parents}})

    code = (f"def run_estimator(request):\n    return {{'echo': request['value'] + {offset}}}\n"
            "def run_sandbox(seed, replicates):\n    return run_estimator({'value': seed})\n"
            if language == "python" else
            f"run_estimator <- function(request) list(echo=request$value+{offset})\n"
            "run_sandbox <- function(seed, replicates) run_estimator(list(value=seed))\n")
    simulation_code = ("def run_sandbox(seed, replicates, estimators):\n"
                       "    return estimators['opaque']({'value': seed + replicates})\n"
                       if language == "python" else
                       "run_sandbox <- function(seed, replicates, estimators) "
                       "estimators[['opaque']](list(value=seed+replicates))\n")
    draft = {"language": language, "execution_profile": "scientific_wasm", "dependencies": [],
             "entrypoint": "run_sandbox", "code": code}
    handoffs = {"problem_card": {"claim_ids": ["opaque_claim"]},
                "theory_derivation_packet": {"claim_index": [{"id": "opaque_claim", "kind": "definition",
                    "document_path": "claim.md", "anchor": "opaque_claim", "depends_on": [], "status": "OPEN"}]}}
    backend.calls = [
        ClientToolCall("document", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                       {"path": "claim.md", "content": "# Opaque record\n\n## opaque_claim\n\nUnresolved, not a scientific result.\n"}),
        ClientToolCall("index", "theory__" + THEORY_WORKSPACE_WRITE_TOOL,
                       {"writes": [{"artifact_name": name, "value": value} for name, value in handoffs.items()]}),
        ClientToolCall("theory-checkpoint", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                       {"readiness_rationale": "Save unresolved work for inspection."}),
        lambda request: select(request, "algorithm", ["theory"]),
        ClientToolCall("algorithm-source", "algorithm__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL, draft),
        ClientToolCall("algorithm-run", "algorithm__" + SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, {"reason": "Inspect exact source."}),
        ClientToolCall("algorithm-checkpoint", "algorithm__" + SCIENTIFIC_SOURCE_COMMIT_TOOL, {}),
        lambda request: select(request, "simulation", ["theory", "algorithm"]),
        ClientToolCall("simulation-source", "simulation__" + SCIENTIFIC_SOURCE_SUBMISSION_TOOL, {**draft, "code": simulation_code}),
        ClientToolCall("simulation-run", "simulation__" + SCIENTIFIC_SOURCE_RUN_CURRENT_TOOL, {"reason": "Invoke exact selected estimator."}),
        ClientToolCall("simulation-checkpoint", "simulation__" + SCIENTIFIC_SOURCE_COMMIT_TOOL, {}),
        lambda request: ClientToolCall("report", "submit_research_result", {
            "report_markdown": "# Execution only\n\nTheory remains unresolved.\n", "selected_checkpoints": references(request),
        }),
    ]
    report = "# Opaque review\n\nclaim.md leaves opaque_claim unresolved. No statistical result is established.\n"
    if include_review:
        review_submission = {"review_report_sha256": hashlib.sha256(report.encode()).hexdigest(),
            "report_evidence_refs": ["theory.document:claim.md", "question"], "overall_verdict": "REVISE",
            "execution_handoff_status": PREFLIGHT_EXECUTION_HANDOFF_NOT_REQUIRED,
            "findings": [{"severity": "high", "category": "unresolved_claim", "summary": "Claim remains unresolved.",
                          "observed_behavior": "The exact document reports an unresolved claim.",
                          "expected_behavior": "No scientific acceptance without resolution.",
                          "evidence_refs": ["theory.document:claim.md"]}]}
        backend.calls[3:3] = [
            ClientToolCall("unbound-review", "theory_review__" + ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL, {"content": report}),
            ClientToolCall("empty-review-inputs", RESEARCH_CONTROL_INPUTS_TOOL, {"scope": "theory_review", "selected_checkpoints": {}}),
            lambda request: select(request, "theory_review", ["theory"]),
            ClientToolCall("review-read", "theory_review__" + THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                           {"path": "claim.md", "line_start": 1, "line_end": 5}),
            ClientToolCall("review-scratch", "theory_review__" + THEORY_SCRATCHPAD_TOOL,
                           {"language": language, "dependencies": [], "code": "print(17)\n" if language == "python" else "cat(17)\n"}),
            ClientToolCall("review-write", "theory_review__" + ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL, {"content": report}),
            ClientToolCall("review-stale-submit", "theory_review__submit_theory_preflight_review",
                           {**review_submission, "review_report_sha256": "0" * 64}),
            ClientToolCall("review-submit", "theory_review__submit_theory_preflight_review", review_submission),
        ]
        backend.calls[-1:-1] = [
            ClientToolCall("different-theory-document", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                           {"path": "claim.md", "content": "# Different opaque record\n\n## opaque_claim\n\nStill unresolved.\n"}),
            ClientToolCall("different-theory-checkpoint", "theory__" + THEORY_WORKSPACE_COMMIT_TOOL,
                           {"readiness_rationale": "Save changed unresolved work."}),
            lambda request: ClientToolCall("stale-final-selection", "submit_research_result", {
                "report_markdown": "# Invalid mixed version selection\n", "selected_checkpoints": references(request),
            }),
        ]
        backend.calls[-1] = lambda request: ClientToolCall("consistent-final-selection", "submit_research_result", {
            "report_markdown": "# Execution only\n\nTheory remains unresolved.\n",
            "selected_checkpoints": {**references(request), "theory": first_theory["hash"]},
        })
    result = run_client_tool_workspace(backend=backend, workspace=workspace)
    resolved = load_research_control_submission(result, question=question, session_dir=tmp_path)
    payloads = resolved["checkpoint_payloads"]
    selected = result.terminal_payload["selected_checkpoints"]
    algorithm_result = payloads["algorithm"]["check_result"]
    simulation_result = payloads["simulation"]["check_result"]
    assert load_theory_workspace_documents(payloads["theory"]["core_packet"])["claim.md"].endswith(
        "Unresolved, not a scientific result.\n")
    assert resolved["report_markdown"] == "# Execution only\n\nTheory remains unresolved.\n"
    assert algorithm_result["prototype"]["source_code"] == code
    assert algorithm_result["prototype"]["metrics"] == {"echo": 7 + offset}
    assert simulation_result["prototype"]["source_code"] == simulation_code
    assert simulation_result["prototype"]["metrics"] == {"echo": 10 + offset}
    assert simulation_result["prototype"]["bound_estimator_code_hashes"] == {"opaque": stable_hash(code)}
    assert simulation_result["prototype"]["estimator_invocation_counts"] == {"opaque": 1}
    assert simulation_result["prototype"]["mechanical_estimator_invocation_verified"] is True
    assert set(selected["simulation"]["inputs"]) == {"algorithm"}
    assert set(selected["simulation"]["provided_inputs"]) == {"theory", "algorithm"}
    assert set(selected["algorithm"]["inputs"]["theory"]["resources"]) == {"estimator:opaque"}
    assert selected["simulation"]["inputs"]["algorithm"]["resources"] == selected["algorithm"]["resources"]
    assert "estimator_interface_contract" in str(backend.requests)
    assert all(row["independent_role_review"] is False and row["empirical_evidence_status"] == "EXPLORATORY_NOT_CONFIRMATORY"
               for row in (algorithm_result, simulation_result))
    assert result.terminal_payload["evidence_role"] == "submission_not_scientific_acceptance"
    if include_review:
        assert payloads["theory_review"]["review_payload"]["review_report_markdown"] == report
        assert payloads["theory_review"]["review_payload"]["overall_verdict"] == "REVISE"
        assert selected["theory_review"]["resources"] == {"report": hashlib.sha256(report.encode()).hexdigest()}
        assert selected["theory_review"]["provided_inputs"]["theory"]["payload_hash"] == selected["theory"]["payload_hash"]
        assert "independent_referee_session" not in str(payloads["theory_review"])
        assert "exact inputs before using its actions" in str(backend.requests[4].messages[-1])
        assert "exactly one selected theory checkpoint" in str(backend.requests[5].messages[-1])
        assert "review_report_sha256 is stale" in str(backend.requests[10].messages[-1])
        assert "17" in str(backend.requests[8].messages[-1])
        assert "THEORY_SCRATCHPAD_EXECUTION_NOT_PROOF_EVIDENCE" in str(backend.requests[8].messages[-1])
        assert "theory.document:claim.md" in str(backend.requests[6].messages[-1])
        assert "selected checkpoint inputs do not match" in str(backend.requests[-1].messages[-1])

    # Exercise the real terminal Critic and persisted graph; this is not a full product/model draw.
    class ScriptedCritic:
        def __init__(self):
            self.calls = []

        def propose(self, **kwargs):
            self.calls.append(kwargs)
            return {"artifact_kind": "CriticEvaluatorProposalPacket", "packet_id": "opaque-assessment",
                    "canonical_evidence_view_hash": kwargs["canonical_evidence_view"]["view_hash"],
                    "research_disposition": {"status": "REJECT" if offset == 0 else "ACCEPT"}}

    critic = ScriptedCritic()
    public_question = research_question_payload(question, include_task_intent=True)
    product_artifacts = {
        "selected-theory": deepcopy(payloads["theory"]["core_packet"]),
        "selected-code": {"artifact_kind": "RuntimeAlgorithmSandboxManifest", "manifest_id": "selected-code",
                          "question": public_question, "theory_packet_id": "selected-theory",
                          "prototypes": [deepcopy(algorithm_result["prototype"])]},
        "selected-simulation": {"artifact_kind": "RuntimeSimulationManifest", "manifest_id": "selected-simulation",
                                "question": public_question, "theory_packet_id": "selected-theory",
                                "generated_simulation_rows": [deepcopy(simulation_result["prototype"])]},
    }
    graph = AgentRuntime(subsystems={"CriticEvaluator": CriticEvaluatorRuntimeSubsystem(proposal_agent=critic)},
                         blackboard=BlackboardState(project_id=question.id, artifacts=product_artifacts))
    product = graph.run(AgentTask(task_id="final-critic", owner_subsystem="CriticEvaluator", objective="Inspect selected artifacts.",
                                 inputs={"question": public_question, "theory_packet_id": "selected-theory",
                                         "algorithm_sandbox_manifest_id": "selected-code",
                                         "simulation_manifest_id": "selected-simulation",
                                         "architect_context": {"evidence_contract": {
                                             "formal_verification_policy": "not_applicable", "formal_required_for_final": False}}}),
                        max_iterations=1).to_json()
    stored_refs, index_path = _persist_runtime_artifact_store(
        artifacts=product["blackboard"]["artifacts"], out_dir=tmp_path / "product", question_id=question.id,
    )
    persisted = {**product, "blackboard": {**product["blackboard"], "artifacts": stored_refs},
                 "blackboard_artifact_payload_policy": "content_addressed_refs", "blackboard_artifact_store_index": str(index_path)}
    result_path = tmp_path / "product" / "result.json"
    result_path.write_text(json.dumps(persisted), encoding="utf-8")
    product_submission = load_runtime_research_submission(load_persisted_runtime_result(result_path), question=question)
    assert len(critic.calls) == 1
    assert product_submission["internal_status"] == ("BLOCKED" if offset == 0 else "ACCEPTED")
    exact_product_row = product_submission["selected_artifacts"]["scientific_code"]["prototypes"][0]
    assert exact_product_row["source_code"] == code
    assert product_submission["selected_artifacts"]["theory"] == payloads["theory"]["core_packet"]

    # The same hidden checks inspect both final sources, independent of internal dispositions.
    submission_before = deepcopy(result.terminal_payload)
    messages_before = deepcopy(backend.requests[-1].messages)
    frozen_draft = payloads["algorithm"]["code_draft"]
    binding = ScientificEstimatorBinding(
        artifact_id="opaque", language=language, code=frozen_draft["code"], code_hash=stable_hash(code),
        dependencies=tuple(frozen_draft["dependencies"]), project_files=tuple(frozen_draft.get("project_files", [])),
        project_hash=selected["algorithm"]["resources"]["project"],
    )
    held_source = ("def run_sandbox(seed, replicates, estimators):\n"
                   "    return estimators['opaque']({'value': seed + replicates})\n"
                   if language == "python" else
                   "run_sandbox <- function(seed, replicates, estimators) "
                   "estimators[['opaque']](list(value=seed+replicates))\n")
    evaluator = {"acceptance_checks": [{"check_id": "opaque-held-value", "path": ["echo"],
                                        "operator": "eq", "expected": 99178}]}
    assert "99173" not in str(backend.requests) and "99178" not in str(backend.requests)
    results = []
    product_binding = replace(binding, code=exact_product_row["source_code"], code_hash=exact_product_row["script_hash"],
                              project_hash=exact_product_row["project_hash"])
    for label, exact_binding in (("selected-shared-source", binding), ("terminal-product-source", product_binding)):
        raw = _run_hidden_scientific_harness(
            sandbox_dir=tmp_path / "evaluator-only" / label, artifact_id=label,
            harness_language=language, harness_code=held_source, harness_dependencies=(),
            estimator_binding=exact_binding, seed=99173, replicates=5, timeout_s=30,
        )
        summary = _hidden_execution_summary(raw, evaluator=evaluator, required_estimator_id="opaque")
        assert summary["execution_passed"] and summary["estimator_invocation_count"] == 1
        assert summary["passed"] is (offset == 0)
        assert raw["estimator_code_hashes"] == {"opaque": stable_hash(code)}
        assert raw["estimator_project_hashes"] == {"opaque": binding.project_hash}
        results.append(raw["metrics"])
    assert results[0] == results[1] == {"echo": 99178 + offset}
    assert len(backend.requests) == (23 if include_review else 12) and not backend.calls
    assert backend.requests[-1].messages == messages_before
    assert result.terminal_payload == submission_before
    assert len(critic.calls) == 1 and critic.calls[0]["canonical_evidence_view"]["view_hash"] == (
        product_submission["selected_artifacts"]["assessment"]["canonical_evidence_view_hash"])
    assert all(row["accepted"] is True for row in (algorithm_result, simulation_result))
    assert "99173" not in str(result.messages) and "99178" not in str(result.messages)


def test_prepared_theory_referee_keeps_frozen_question_material_and_disposition(tmp_path):
    question = OpenResearchQuestion("opaque-review", "Opaque target", "Inspect an unresolved claim.",
        task_intent={"theory": "required", "scientific_code": "not_applicable", "empirical": "not_applicable", "formal": "not_applicable"})
    root = tmp_path / "run" / "theory_workspaces" / "draft"
    root.mkdir(parents=True)
    body = "# Opaque target\n\n## C\n\nThe claim is unresolved.\n"
    (root / "claim.md").write_text(body, encoding="utf-8")
    core = {"problem_card": {"claim_ids": ["C"]},
            "theory_derivation_packet": {"claim_index": [{"id": "C", "kind": "theorem", "status": "OPEN", "document_path": "claim.md"}]},
            "theory_workspace_manifest": theory_workspace_document_manifest({"claim.md": body}, workspace_dir=root)}
    material = build_theory_informed_metric_protocol_material(theory_packet=core, theory_packet_id="opaque-parent")
    contract = {"dimension_requirements": deepcopy(question.task_intent)}
    report = "# Review\n\nclaim.md leaves C unresolved; no scientific result is established.\n"
    backend = Scripted([
        ClientToolCall("read", THEORY_WORKSPACE_READ_DOCUMENT_TOOL, {"path": "claim.md", "line_start": 1, "line_end": 5}),
        ClientToolCall("write", ARCHITECT_THEORY_EXECUTION_PREFLIGHT_WRITE_REPORT_TOOL, {"content": report}),
        ClientToolCall("submit", "submit_theory_preflight_review", {
            "review_report_sha256": hashlib.sha256(report.encode()).hexdigest(), "report_evidence_refs": ["theory.document:claim.md"],
            "overall_verdict": "REVISE", "execution_handoff_status": PREFLIGHT_EXECUTION_HANDOFF_NOT_REQUIRED,
            "findings": [{"severity": "high", "category": "unresolved_claim", "summary": "C is unresolved.",
                          "observed_behavior": "No derivation is supplied.", "expected_behavior": "Report this gap honestly.",
                          "evidence_refs": ["theory.document:claim.md"]}],
        }),
    ])
    workspace = prepare_architect_theory_execution_preflight_workspace(
        provider=backend, question=question, theory_protocol_material=material, upstream_research_contract=contract,
        model=MODEL, model_tier="local", provider_name="local", max_tokens=1024, temperature=0,
    )
    assert not backend.requests
    expected = workspace.initial_context["review_input_fingerprint"]
    question.task_intent["formal"] = "required"
    material["source_theory_packet_hash"] = "later-changed-packet"
    contract["dimension_requirements"]["formal"] = "required"
    packet = run_client_tool_workspace(backend=backend, workspace=workspace)
    assert packet["question_id"] == "opaque-review"
    assert packet["source_theory_packet_hash"] == stable_hash(core)
    assert packet["review_input_fingerprint"] == expected
    assert packet["overall_verdict"] == "REVISE" and packet["kernel_verified"] is False
    assert packet["review_scope"]["formal_sources_applicable"] is False
    assert "claim.md" in workspace.initial_context["review_instructions"]
    assert len(backend.requests) == 3 and not backend.calls


def test_application_control_preserves_an_honest_gap_without_fabricating_a_theory_checkpoint(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    question = OpenResearchQuestion("opaque-gap", "Opaque gap", "An unresolved task.",
                                    task_intent={"theory": "required", "scientific_code": "not_applicable",
                                                 "empirical": "not_applicable", "formal": "not_applicable"})
    backend = Scripted([
        ClientToolCall("document", "theory__" + THEORY_WORKSPACE_WRITE_DOCUMENT_TOOL,
                       {"path": "gap.md", "content": "# Unresolved opaque record\n"}),
        ClientToolCall("read", "theory__" + THEORY_WORKSPACE_READ_DOCUMENT_TOOL,
                       {"path": "gap.md", "line_start": 1, "line_end": 1}),
        ClientToolCall("gap", "theory__" + THEORY_WORKSPACE_GAP_TOOL,
                       {"summary": "Unresolved, not established.", "blocking_claims": [],
                        "evidence_refs": ["gap.md"], "next_step": "Further investigation needed."}),
        ClientToolCall("report", "submit_research_result",
                       {"report_markdown": "# Honest gap\n", "selected_checkpoints": {}}),
    ])
    workspace = prepare_single_context_research_workspace(
        question=question, request=ClientToolTurnRequest(system_prompt="Common task.", messages=(), tools=(),
                                                       model=MODEL, max_tokens=1024),
        theory_agent=LLMTheoryDeveloperAgent(provider=backend, config=ResearchArchitectConfig(
            provider_name="local", model=MODEL, model_tier="local", serious_model=MODEL, serious_model_tier="local",
            max_tokens=1024, temperature=0)),
        algorithm_agent=LLMAlgorithmEngineerAgent(provider=backend, config=AlgorithmEngineerConfig(
            provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0)),
        simulation_agent=LLMSimulationEngineerAgent(provider=backend, config=SimulationEngineerConfig(
            provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0)),
        estimator_id="opaque", session_dir=tmp_path, session_id="gap-app", n_runs=3, seed=7, timeout_s=30,
        max_turns=8, max_tool_calls=8, max_no_progress_turns=8,
    )
    result = run_client_tool_workspace(backend=backend, workspace=workspace)
    raw = json.loads((tmp_path / result.observation_refs[2]["relative_path"]).read_text())
    assert raw["terminal_payload"]["disposition"] == "THEORY_GAP"
    assert raw["terminal_payload"]["theory_gap"]["summary"] == "Unresolved, not established."
    assert not raw["model_content_blocks"]
    assert result.terminal_payload["selected_checkpoints"] == {}
    assert result.terminal_payload["task_intent"]["theory"] == "required"
    assert not (tmp_path / "execution").exists()

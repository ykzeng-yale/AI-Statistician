"""Declared draw entry with mocked native HTTP, not an inference or science study."""

from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from ai_statistician.fingerprint import stable_hash
from benchmarks.publication.draw_cli import main


MODEL = "Qwen3-4B-Instruct-2507"


def write_reference(path, value):
    raw = (json.dumps(value) + "\n").encode()
    path.write_bytes(raw)
    return {"path": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}


def configuration(tmp_path, monkeypatch, *, workflow="", reviewers=False):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    question = {"id": "opaque-cli", "title": "Opaque entry", "description": "Unresolved mechanism fixture.",
                "task_intent": {"theory": "required", "scientific_code": "not_applicable",
                                "empirical": "not_applicable", "formal": "not_applicable"}}
    common = dict(provider_name="local", model=MODEL, model_tier="local", max_tokens=1024, temperature=0)
    roles = {"theory": {**common, "serious_model": MODEL, "serious_model_tier": "local"},
             "algorithm": dict(common), "simulation": dict(common)}
    if reviewers:
        roles.update(theory_reviewer=dict(common), code_reviewer=dict(common))
    config = {"question_ref": write_reference(tmp_path / "questions.json", [question]), "question_id": question["id"],
              "deployment_ref": write_reference(tmp_path / "deployment.json", {
                  "model": MODEL, "weights_sha256": "fixture_declaration_not_a_live_deployment",
                  "runtime": "mocked_native_HTTP", "chat_template_sha256": "fixture"}),
              "mode": "same_workflow" if workflow else "free_planning", "workflow_instructions": workflow,
              "backend": {"base_url": "http://127.0.0.1:8081/v1", "timeout_s": 30},
              "request": {"system_prompt": "Research the supplied question.", "model": MODEL, "max_tokens": 1024,
                          "temperature": 0, "tool_choice": "auto"},
              "roles": roles, "estimator_ids": ["opaque"],
              "execution": {"n_runs": 3, "seed": 7, "timeout_s": 30, "confirmatory_seeds": [918007, 918011]},
              "limits": {"max_turns": 8, "max_tool_calls": 8, "max_no_progress_turns": 8, "local_model_call_limit": 8}}
    return config


def invoke(tmp_path, config):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return main(["--config", str(path), "--out", str(tmp_path / "draw")])


def wire(monkeypatch, tmp_path, actions, *, failure="", mutate=None):
    requests, freezes = [], []

    class Opener:
        def open(self, request, *, timeout):
            frozen = json.loads((tmp_path / "draw" / "frozen_draw.json").read_text())
            assert frozen["frozen_draw_hash"] == stable_hash({key: value for key, value in frozen.items()
                                                            if key != "frozen_draw_hash"})
            assert frozen["study_provenance"]["deployment_authority"] == "caller_declaration_not_live_attestation_or_scientific_qualification"
            config_ref = frozen["study_provenance"]["config_ref"]
            if not requests:
                assert hashlib.sha256(Path(config_ref["path"]).read_bytes()).hexdigest() == config_ref["sha256"]
            freezes.append(frozen)
            payload = json.loads(request.data)
            assert "918007" not in json.dumps(payload) and "918011" not in json.dumps(payload)
            requests.append(payload)
            if mutate:
                mutate()
            if failure == "http":
                raise HTTPError(request.full_url, 400, "Bad Request", {}, BytesIO(b'opaque transport failure'))
            action = actions.pop(0)
            name, arguments = action(payload) if callable(action) else action
            return BytesIO(json.dumps({"model": "other-model" if failure == "model" else MODEL,
                "choices": [{"message": {"content": "", "tool_calls": [{"id": "call-" + str(len(requests)),
                    "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}]},
                    "finish_reason": "tool_calls"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}).encode())

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    return requests, freezes


def select_observed(scope, report):
    def final(payload):
        for row in reversed(payload["messages"]):
            if row["role"] != "tool":
                continue
            content = json.loads(row["content"])["content"]
            if isinstance(content, list):
                for part in content:
                    ref = json.loads(part["text"]).get("shared_checkpoint_ref", {})
                    if ref.get("scope") == scope:
                        return "submit_research_result", {"selected_checkpoints": {scope: ref["payload_hash"]},
                                                         "report_markdown": report}
        raise AssertionError("actual checkpoint observation missing")
    return final


@pytest.mark.parametrize("workflow", ["", "Follow the same prospectively declared workflow."])
@pytest.mark.parametrize("reviewers", [False, True])
def test_cli_freezes_declared_inputs_and_keeps_partial_submission_partial(tmp_path, monkeypatch, capsys, workflow, reviewers):
    config = configuration(tmp_path, monkeypatch, workflow=workflow, reviewers=reviewers)
    report = "# Honest final\n\nAll scientific questions remain unresolved.\n"
    requests, freezes = wire(monkeypatch, tmp_path, [("submit_research_result", {
        "selected_checkpoints": {}, "report_markdown": report})],
        mutate=lambda: (tmp_path / "questions.json").write_text("changed after first call"))
    assert invoke(tmp_path, config) == 0
    summary = json.loads(capsys.readouterr().out)
    ref = summary["final_material_ref"]
    raw = Path(ref["path"]).read_bytes()
    assert ref["sha256"] == hashlib.sha256(raw).hexdigest() and ref["byte_size"] == len(raw)
    final = json.loads(raw)
    assert final["submission_identity"]["selected_checkpoints"] == {}
    assert final["report_markdown"] == report
    assert final["material"] == {"theory_documents": [], "estimator_bindings": [], "empirical_artifact": None}
    assert final["authority"] == "selected_final_material_not_scientific_acceptance"
    assert summary["status"] == "REROUTE" and summary["scientific_evaluation_performed"] is False
    assert summary["local_model_usage"]["attempted_requests"] == len(requests) == 1
    frozen = freezes[0]
    assert frozen["question"]["description"] == "Unresolved mechanism fixture."
    assert frozen["study_provenance"]["question_ref"]["sha256"] == config["question_ref"]["sha256"]
    assert frozen["study_provenance"]["declared_deployment"]["runtime"] == "mocked_native_HTTP"
    assert set(frozen["role_configs"]) == set(config["roles"])
    names = {row["function"]["name"] for row in requests[0]["tools"]}
    assert ("code_review__run_exact_estimator_review_probe" in names) is reviewers
    saved = {path: path.read_bytes() for path in (tmp_path / "draw").rglob("*") if path.is_file()}
    with pytest.raises(FileExistsError):
        invoke(tmp_path, config)
    assert len(requests) == 1 and all(path.read_bytes() == value for path, value in saved.items())


def test_cli_projects_only_observed_selected_markdown_not_the_latest_working_file(tmp_path, monkeypatch, capsys):
    config = configuration(tmp_path, monkeypatch)
    document = "# Unresolved derivation\n\n## C\n\nA reviewable open claim, not a mathematical result.\n"

    requests, freezes = wire(monkeypatch, tmp_path, [
        ("theory__write_theory_document", {"path": "claim.md", "content": document}),
        ("theory__write_theory_workspace", {"writes": [
            {"artifact_name": "problem_card", "value": {"claim_ids": ["C"]}},
            {"artifact_name": "theory_derivation_packet", "value": {"claim_index": [{
                "id": "C", "kind": "definition", "document_path": "claim.md", "anchor": "C", "depends_on": [], "status": "OPEN"}]}}]}),
        ("theory__commit_theory_checkpoint", {"readiness_rationale": "Checkpoint for independent review only."}),
        ("theory__write_theory_document", {"path": "claim.md", "content": "# Later unselected note\n"}),
        select_observed("theory", "# Selected earlier checkpoint\n"),
    ])
    assert invoke(tmp_path, config) == 0
    summary = json.loads(capsys.readouterr().out)
    saved = json.loads(Path(summary["final_material_ref"]["path"]).read_text())
    assert saved["material"]["theory_documents"] == [{"path": "claim.md", "content": document,
        "sha256": hashlib.sha256(document.encode()).hexdigest()}]
    assert saved["material"]["estimator_bindings"] == [] and saved["material"]["empirical_artifact"] is None
    assert len(requests) == 5 and all(row == freezes[0] for row in freezes)


@pytest.mark.parametrize("language", ["python", "r"])
def test_cli_serializes_exact_selected_executed_source_without_scientific_credit(tmp_path, monkeypatch, capsys, language):
    from ai_statistician.scientific_project import scientific_project_hash
    from ai_statistician.scientific_sandbox import discover_scientific_sandbox_runtime

    runtime = discover_scientific_sandbox_runtime()
    if not (runtime.python_available if language == "python" else runtime.r_available):
        pytest.skip("scientific runtime unavailable")
    config = configuration(tmp_path, monkeypatch)
    code = ("def run_estimator(request):\n    return {}\ndef run_sandbox(seed, replicates):\n    return {'opaque': seed + replicates}\n"
            if language == "python" else
            "run_estimator <- function(request) list()\nrun_sandbox <- function(seed, replicates) list(opaque=seed+replicates)\n")
    draft = {"language": language, "execution_profile": "scientific_wasm", "dependencies": [],
             "entrypoint": "run_sandbox", "code": code}
    requests, _ = wire(monkeypatch, tmp_path, [
        ("select_workspace_inputs", {"scope": "algorithm", "selected_checkpoints": {}}),
        ("algorithm__submit_scientific_source", draft),
        ("algorithm__run_current_scientific_source", {"reason": "Inspect the actual opaque source."}),
        ("algorithm__commit_scientific_source", {}),
        ("algorithm__submit_scientific_source", {**draft, "code": code + "\n# Later unselected source\n"}),
        select_observed("algorithm", "# Execution only\n\nTheory and experiment remain missing.\n"),
    ])
    assert invoke(tmp_path, config) == 0
    summary = json.loads(capsys.readouterr().out)
    final = json.loads(Path(summary["final_material_ref"]["path"]).read_text())
    assert final["material"]["estimator_bindings"] == [{
        "artifact_id": "opaque", "language": language, "code": code, "code_hash": stable_hash(code),
        "dependencies": [], "project_files": [],
        "project_hash": scientific_project_hash(language=language, code=code, project_files=[])}]
    assert final["material"]["theory_documents"] == [] and final["material"]["empirical_artifact"] is None
    assert summary["scientific_evaluation_performed"] is False and len(requests) == 6


@pytest.mark.parametrize("failure", ["budget", "http", "model"])
def test_cli_records_failure_without_another_draw_or_final_material(tmp_path, monkeypatch, capsys, failure):
    config = configuration(tmp_path, monkeypatch)
    config["limits"]["local_model_call_limit"] = 1
    requests, _ = wire(monkeypatch, tmp_path, [("theory__write_theory_document", {
        "path": "claim.md", "content": "# Saved incomplete work\n"})], failure=failure)
    assert invoke(tmp_path, config) == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == ("BLOCKED" if failure == "budget" else "FAILED")
    assert summary["final_material_ref"] is None and not (tmp_path / "draw" / "final_material.json").exists()
    assert len(requests) == summary["local_model_usage"]["attempted_requests"] == 1
    assert json.loads((tmp_path / "draw" / "runtime_result.json").read_text())["blackboard"]["evidence_ledger"] == []


@pytest.mark.parametrize("defect", ["question_hash", "question_size", "deployment_hash", "deployment_size", "wrong_deployment",
    "duplicate_question", "absent_question", "mode", "missing_workflow", "extra_workflow", "cloud_endpoint", "cloud_role",
    "serious_model", "role_model", "role_temperature", "missing_owner", "unknown_role", "unknown_field", "unknown_execution"])
def test_invalid_declaration_never_calls_any_model(tmp_path, monkeypatch, defect):
    config = configuration(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr("urllib.request.build_opener", lambda *args: calls.append(args))
    if defect in {"question_hash", "question_size", "deployment_hash", "deployment_size"}:
        ref = config["question_ref" if defect.startswith("question") else "deployment_ref"]
        ref["sha256" if defect.endswith("hash") else "byte_size"] = "incorrect" if defect.endswith("hash") else ref["byte_size"] + 1
    elif defect == "wrong_deployment":
        config["deployment_ref"] = write_reference(tmp_path / "deployment.json", {"model": "other-model"})
    elif defect == "duplicate_question":
        rows = json.loads((tmp_path / "questions.json").read_text())
        config["question_ref"] = write_reference(tmp_path / "questions.json", rows + deepcopy(rows))
    elif defect == "absent_question":
        config["question_id"] = "absent"
    elif defect == "mode":
        config["mode"] = "unsupported"
    elif defect == "missing_workflow":
        config["mode"] = "same_workflow"
    elif defect == "extra_workflow":
        config["workflow_instructions"] = "Not free-planning."
    elif defect == "cloud_endpoint":
        config["backend"]["base_url"] = "https://example.org/v1"
    elif defect == "cloud_role":
        config["roles"]["algorithm"]["provider_name"] = "anthropic"
    elif defect == "serious_model":
        config["roles"]["theory"]["serious_model"] = "other-model"
    elif defect == "role_model":
        config["roles"]["simulation"]["model"] = "other-model"
    elif defect == "role_temperature":
        config["roles"]["algorithm"]["temperature"] = 0.5
    elif defect == "missing_owner":
        del config["roles"]["theory"]
    elif defect == "unknown_role":
        config["roles"]["extra"] = dict(config["roles"]["algorithm"])
    elif defect == "unknown_field":
        config["extra"] = "not supported"
    elif defect == "unknown_execution":
        config["execution"]["extra"] = "not supported"
    with pytest.raises((ValueError, TypeError)):
        invoke(tmp_path, config)
    assert calls == [] and not (tmp_path / "draw").exists()


@pytest.mark.parametrize("source", ["snapshot", "discovery", "both"])
def test_source_access_is_declared_before_calls_not_a_hidden_baseline_hint(tmp_path, monkeypatch, capsys, source):
    config = configuration(tmp_path, monkeypatch, reviewers=True)
    if source in {"snapshot", "both"}:
        root = tmp_path / "sources"
        root.mkdir()
        content = "# Opaque permitted source\nNo hidden theorem or answer.\n"
        (root / "record.md").write_text(content)
        config["source_snapshot_ref"] = write_reference(tmp_path / "sources.json", {
            "schema_version": 1, "snapshot_id": "opaque", "source_horizon": "2026-01-01", "source_root": "sources",
            "documents": [{"document_id": "opaque-source", "title": "Opaque source", "source_kind": "paper",
                "relative_path": "record.md", "sha256": hashlib.sha256(content.encode()).hexdigest(), "model_visible": True,
                "publication_date": "2025-01-01", "citation": "Mechanism fixture", "license": "CC0-1.0"}]})
    if source in {"discovery", "both"}:
        config["source_discovery"] = {"source_horizon": "2026-01-01", "state_dir": "fresh-discovery"}
    requests, freezes = wire(monkeypatch, tmp_path, [("submit_research_result", {
        "selected_checkpoints": {}, "report_markdown": "# No sources used\n"})])
    assert invoke(tmp_path, config) == 0
    capsys.readouterr()
    provenance = freezes[0]["study_provenance"]
    assert bool(provenance["source_snapshot"]) is (source in {"snapshot", "both"})
    assert bool(provenance["source_discovery"]) is (source in {"discovery", "both"})
    if provenance["source_discovery"]:
        assert provenance["source_discovery"]["strict_historical_benchmark_authority"] is False
        assert provenance["source_discovery"]["state_dir"] == str(tmp_path / "fresh-discovery")
    assert len(requests) == 1


@pytest.mark.parametrize("directory", ["existing-discovery", "draw/discovery"])
def test_discovery_cannot_reuse_another_draw_or_precreate_this_one(tmp_path, monkeypatch, directory):
    config = configuration(tmp_path, monkeypatch)
    config["source_discovery"] = {"source_horizon": "2026-01-01", "state_dir": directory}
    if directory == "existing-discovery":
        (tmp_path / directory).mkdir()
    with pytest.raises(ValueError, match="fresh and outside"):
        invoke(tmp_path, config)
    assert not (tmp_path / "draw").exists()


def collaborative_configuration(tmp_path, monkeypatch):
    config = configuration(tmp_path, monkeypatch, reviewers=True)
    for key in ("request", "workflow_instructions", "estimator_ids", "execution", "limits"):
        del config[key]
    question = json.loads((tmp_path / "questions.json").read_text())[0]
    question["task_intent"].update(source_replication="not_applicable", novelty="not_applicable")
    config["question_ref"] = write_reference(tmp_path / "questions.json", [question])
    config["mode"] = "full_collaboration"
    common = dict(config["roles"]["algorithm"])
    config["roles"].update(architect={**common, "metric_semantic_reviewer_model": MODEL,
        "metric_semantic_reviewer_model_tier": "local"}, critic=dict(common))
    config["runtime"] = {"evaluation_mode": "research_eval", "evaluation_provider": "local",
        "evaluation_model_tier": "local", "evaluation_model": MODEL, "max_iterations": 4,
        "local_model_call_limit": 1, "n_runs": 3, "seed": 7, "theory_scratch_enabled": False}
    config["architect_context"] = {"opaque_declared_context": "not a scientific answer"}
    return config


@pytest.mark.parametrize("mode", ["full_collaboration", "no_cross_role_revision"])
@pytest.mark.parametrize("failure", ["budget", "http", "model"])
def test_full_cli_runs_actual_production_graph_with_one_shared_local_budget(tmp_path, monkeypatch, capsys, failure, mode):
    config = collaborative_configuration(tmp_path, monkeypatch)
    config["mode"] = mode
    requests, freezes = wire(monkeypatch, tmp_path, [("write_theory_document", {
        "path": "claim.md", "content": "# Incomplete production work\n"})], failure=failure)
    assert invoke(tmp_path, config) == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "BLOCKED"
    assert summary["final_material_ref"] is None and summary["scientific_evaluation_performed"] is False
    assert summary["local_model_usage"]["attempted_requests"] == len(requests) == 1
    if failure == "budget":
        assert summary["local_model_usage"]["denied_requests"] == 1
    frozen = freezes[0]
    assert frozen["mode"] == mode
    assert frozen["intervention"] == ("no_cross_role_revision_v1" if mode == "no_cross_role_revision" else None)
    assert frozen["runtime_config"]["local_model_call_limit"] == 1
    assert frozen["architect_context"] == config["architect_context"]
    assert set(frozen["role_configs"]) == set(config["roles"])
    assert {row["function"]["name"] for row in requests[0]["tools"]} >= {"write_theory_document", "commit_theory_checkpoint"}
    assert all(not row["function"]["name"].startswith("theory__") for row in requests[0]["tools"])
    from ai_statistician.agent_runtime import load_persisted_runtime_result
    paths = list((tmp_path / "draw" / "author").glob("*_runtime_result.json"))
    assert len(paths) == 1
    result = load_persisted_runtime_result(paths[0])
    assert result["blackboard"]["evidence_ledger"]
    assert all(row["status"] == "VALIDATION_FAILED_RECORDED_NOT_THEORY_OR_PROOF_EVIDENCE"
               for row in result["blackboard"]["evidence_ledger"])
    assert bool(result["pending_task"]) is (failure == "budget")
    assert result["traces"][0]["subsystem"] == "TheoryDeveloper"
    assert not (tmp_path / "draw" / "final_material.json").exists()
    saved = {path: path.read_bytes() for path in (tmp_path / "draw").rglob("*") if path.is_file()}
    with pytest.raises(FileExistsError):
        invoke(tmp_path, config)
    assert len(requests) == 1 and all(path.read_bytes() == raw for path, raw in saved.items())


@pytest.mark.parametrize("defect", ["missing_reviewer", "critic_cloud", "architect_review_model", "runtime_model",
                                  "runtime_provider", "debug", "budget_zero", "budget_bool", "required_formal", "control_request"])
def test_full_cli_rejects_invalid_composition_before_inference(tmp_path, monkeypatch, defect):
    config = collaborative_configuration(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr("urllib.request.build_opener", lambda *args: calls.append(args))
    if defect == "missing_reviewer":
        del config["roles"]["theory_reviewer"]
    elif defect == "critic_cloud":
        config["roles"]["critic"]["provider_name"] = "anthropic"
    elif defect == "architect_review_model":
        config["roles"]["architect"]["metric_semantic_reviewer_model"] = "other-model"
    elif defect == "runtime_model":
        config["runtime"]["evaluation_model"] = "other-model"
    elif defect == "runtime_provider":
        config["runtime"]["evaluation_provider"] = "anthropic"
    elif defect == "debug":
        config["runtime"]["evaluation_mode"] = "debug"
    elif defect in {"budget_zero", "budget_bool"}:
        config["runtime"]["local_model_call_limit"] = 0 if defect == "budget_zero" else True
    elif defect == "required_formal":
        question = json.loads((tmp_path / "questions.json").read_text())[0]
        question["task_intent"]["formal"] = "required"
        config["question_ref"] = write_reference(tmp_path / "questions.json", [question])
    else:
        config["request"] = {}
    with pytest.raises((ValueError, TypeError)):
        invoke(tmp_path, config)
    assert calls == [] and not (tmp_path / "draw").exists()


def scripted_terminal(monkeypatch, *, status, defect="", request_replan=False):
    """Scripted sole-runtime/persistence fixture, never a model or acceptance claim."""
    from ai_statistician.agent_runtime import AgentRuntime, AgentStepResult, AgentTask, BlackboardState, runtime_artifact_reference
    from ai_statistician.research_agent_runtime import _persist_runtime_artifact_store
    from ai_statistician.research_schema import research_question_payload

    assessment = {"artifact_kind": "CriticEvaluatorProposalPacket", "packet_id": "assessment",
                  "canonical_evidence_view_hash": "opaque-view", "opaque_referee_note": "All scientific questions unresolved."}

    def run(questions, out_dir, **kwargs):
        question = questions[0]
        assert kwargs["architect_coordinator"].metric_semantic_reviewer.provider is kwargs["theory_developer"].provider
        board = BlackboardState(project_id="scripted-production-selection")
        board.artifacts["unselected"] = {"artifact_kind": "OpaqueTheory", "content": "never substitute this"}

        class FinalCritic:
            name = "CriticEvaluator"

            def run(self, task, blackboard):
                manifest = {"artifact_kind": "RuntimeCriticEvaluatorManifest", "manifest_id": "critic",
                    "question": research_question_payload(question, include_task_intent=True),
                    "llm_critic_evaluator_proposal_id": "assessment", "canonical_evidence_view_hash": "opaque-view",
                    "submission_artifact_refs": {"assessment": runtime_artifact_reference("assessment", assessment)}}
                if defect == "selection":
                    manifest["submission_artifact_refs"]["assessment"]["content_hash"] = "different"
                return AgentStepResult(status=status, rationale="Scripted terminal, no scientific adjudication.",
                    next_task=AgentTask("replan", "ArchitectCoordinator", "Choose a revision.",
                        inputs={"runtime_architect_operation": "environment_feedback_route"}) if request_replan else None,
                    produced_artifacts={"assessment": assessment, **({} if defect == "no_submission" else {"critic": manifest})})

        result = AgentRuntime(subsystems={"CriticEvaluator": FinalCritic()}, blackboard=board,
            handoff_policy=kwargs.get("handoff_policy")).run(
            AgentTask("final", "CriticEvaluator", "Collect an unresolved fixture."), max_iterations=1,
            local_model_call_limit=kwargs["config"].local_model_call_limit)
        persisted = result.to_json()
        refs, index = _persist_runtime_artifact_store(artifacts=board.artifacts, out_dir=out_dir, question_id=question.id)
        persisted["blackboard"]["artifacts"] = refs
        persisted["blackboard_artifact_payload_policy"] = "content_addressed_refs"
        persisted["blackboard_artifact_store_index"] = str(index)
        path = out_dir / "scripted_runtime_result.json"
        path.write_text(json.dumps(persisted))
        if defect == "stored_hash":
            Path(refs["assessment"]["path"]).write_text(json.dumps({**assessment, "opaque_referee_note": "changed"}))
        return {"artifacts": {"per_question_results": [str(path)]}}

    monkeypatch.setattr("benchmarks.publication.run_collaborative_draw.run_research_agent_runtime", run)
    return assessment


@pytest.mark.parametrize("status", ["ACCEPTED", "BLOCKED", "FAILED"])
def test_full_cli_collects_only_bound_final_selection_without_promoting_internal_verdict(tmp_path, monkeypatch, capsys, status):
    config = collaborative_configuration(tmp_path, monkeypatch)
    assessment = scripted_terminal(monkeypatch, status=status)
    assert invoke(tmp_path, config) == 0
    summary = json.loads(capsys.readouterr().out)
    ref = summary["final_material_ref"]
    raw = Path(ref["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ref["sha256"] and len(raw) == ref["byte_size"]
    material = json.loads(raw)
    assert material["assessment"] == assessment and "report_markdown" not in material
    assert material["source_kind"] == "runtime"
    assert material["submission_identity"]["internal_status"] == status
    assert set(material["submission_identity"]["selected_artifact_refs"]) == {"assessment"}
    assert material["material"] == {"theory_documents": [], "estimator_bindings": [], "empirical_artifact": None}
    assert summary["scientific_evaluation_performed"] is False and summary["local_model_usage"]["attempted_requests"] == 0
    assert material["authority"] == "selected_final_material_not_scientific_acceptance"


@pytest.mark.parametrize("defect", ["no_submission", "selection", "stored_hash"])
def test_full_cli_does_not_salvage_absent_or_changed_terminal_material(tmp_path, monkeypatch, capsys, defect):
    config = collaborative_configuration(tmp_path, monkeypatch)
    scripted_terminal(monkeypatch, status="BLOCKED", defect=defect)
    if defect == "no_submission":
        assert invoke(tmp_path, config) == 1
        assert json.loads(capsys.readouterr().out)["final_material_ref"] is None
    else:
        with pytest.raises(ValueError):
            invoke(tmp_path, config)
    assert not (tmp_path / "draw" / "final_material.json").exists()


@pytest.mark.parametrize("mode", ["full_collaboration", "no_cross_role_revision"])
def test_cli_actual_runtime_uses_declared_revision_policy_before_a_second_author_invocation(tmp_path, monkeypatch, capsys, mode):
    from dataclasses import replace
    from ai_statistician.agent_runtime import AgentStepResult, AgentTask, agent_task_reference, load_persisted_runtime_result, materialize_agent_task_continuation
    from ai_statistician import research_agent_runtime as runtime

    config = collaborative_configuration(tmp_path, monkeypatch)
    config["mode"] = mode
    calls, producer = [], []

    def theory(self, task, board):
        calls.append("theory")
        return AgentStepResult(status="REROUTE", rationale="Opaque forward source handoff.",
            next_task=AgentTask("algorithm", "AlgorithmEngineer", "Opaque source.", inputs={"question": task.inputs["question"]}))

    def algorithm(self, task, board):
        calls.append("algorithm")
        if producer:
            return AgentStepResult(status="BLOCKED", rationale="Opaque revised source, no scientific acceptance.",
                produced_artifacts={"revised": {"source": "MODEL-AUTHORED-OPAQUE-REVISION"}})
        producer.append(task)
        cid, continuation, artifacts = materialize_agent_task_continuation(task)
        work_order = {"artifact_kind": "RuntimeGeneratedCodeSemanticReviewWorkOrder", "source_subsystem": task.owner_subsystem,
            "source_task_id": task.task_id, "source_task_ref": agent_task_reference(task),
            "source_task_continuation_id": cid, "source_task_continuation_hash": stable_hash(continuation)}
        return AgentStepResult(status="REROUTE", rationale="Opaque source requires independent review.",
            produced_artifacts={**artifacts, "work-order": work_order, "source": {"source": "UNCHANGED ORIGINAL"}},
            next_task=AgentTask("review", "GeneratedCodeSemanticReviewer", "Opaque review.",
                inputs={"work_order_id": "work-order", "work_order_hash": stable_hash(work_order)}))

    def reviewer(self, task, board):
        calls.append("reviewer")
        source = producer[0]
        return AgentStepResult(status="REVISE", rationale="Opaque source-bound critique.", next_task=replace(source,
            task_id="algorithm-revision", inputs={**source.inputs, "generated_code_semantic_review_revision_count": 1,
                "environment_feedback": {"feedback_type": "generated_code_semantic_review_feedback", "source_subsystem": source.owner_subsystem,
                    "semantic_review_execution_id": "execution", "semantic_review_packet_id": "review",
                    "semantic_review_packet_hash": "opaque-review-hash"}}))

    monkeypatch.setattr(runtime.TheoryDeveloperRuntimeSubsystem, "run", theory)
    monkeypatch.setattr(runtime.AlgorithmEngineerRuntimeSubsystem, "run", algorithm)
    monkeypatch.setattr(runtime.GeneratedCodeSemanticReviewerRuntimeSubsystem, "run", reviewer)
    assert invoke(tmp_path, config) == 1
    assert json.loads(capsys.readouterr().out)["final_material_ref"] is None
    assert calls == ["theory", "algorithm", "reviewer"] + (["algorithm"] if mode == "full_collaboration" else [])
    path = next((tmp_path / "draw" / "author").glob("*_runtime_result.json"))
    result = load_persisted_runtime_result(path)
    assert result["blackboard"]["artifacts"]["source"] == {"source": "UNCHANGED ORIGINAL"}
    assert ("revised" in result["blackboard"]["artifacts"]) is (mode == "full_collaboration")
    assert result["local_model_usage"]["attempted_requests"] == 0
    assert result["blackboard"]["evidence_ledger"] == []
    if mode == "no_cross_role_revision":
        assert result["traces"][-1]["failure_classification"] == "publication_cross_role_revision_disabled"


def test_ablated_critic_replan_keeps_exact_final_assessment_not_an_accepted_replacement(tmp_path, monkeypatch, capsys):
    config = collaborative_configuration(tmp_path, monkeypatch)
    config["mode"] = "no_cross_role_revision"
    assessment = scripted_terminal(monkeypatch, status="REROUTE", request_replan=True)
    assert invoke(tmp_path, config) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "BLOCKED" and summary["scientific_evaluation_performed"] is False
    final = json.loads(Path(summary["final_material_ref"]["path"]).read_text())
    assert final["assessment"] == assessment and final["submission_identity"]["internal_status"] == "BLOCKED"
    assert final["material"] == {"theory_documents": [], "estimator_bindings": [], "empirical_artifact": None}

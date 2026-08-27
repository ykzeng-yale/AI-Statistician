from __future__ import annotations

from dataclasses import asdict, replace

import ai_statistician.research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import (
    AgentTask,
    BlackboardState,
    RUNTIME_CONTINUATION_BUDGET_MARKER_KEY,
    ToolCallRecord,
    resolve_runtime_artifact_references,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.scientific_code_workspace import (
    SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_KIND,
    ScientificCodeWorkspaceResult,
    runtime_scientific_workspace_resume_plan,
    scientific_workspace_resume_plan,
    scientific_workspace_progress_continuation,
    scientific_workspace_progress_result,
)
from ai_statistician.simulation_engineer_llm import (
    LLMSimulationEngineerAgent,
    SimulationEngineerConfig,
)


def _checkpoint(*, question_id: str, source_id: str) -> dict:
    draft = {
        "language": "python",
        "execution_profile": "stdlib",
        "dependencies": [],
        "entrypoint": "run_sandbox",
        "code": "def run_sandbox(seed, replicates):\n    return missing\n",
    }
    draft_hash = stable_hash(draft)
    last_check = {
        "code_draft_hash": draft_hash,
        "accepted": False,
        "stderr": "NameError: missing",
    }
    body = {
        "schema_version": 2,
        "artifact_kind": SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_KIND,
        "artifact_id": f"{question_id}:{source_id}",
        "workspace_operation": "initial_authoring",
        "parent_code_draft_hash": "",
        "current_code_draft_hash": draft_hash,
        "current_code_draft": draft,
        "observed_code_draft_hashes": [draft_hash],
        "source_updates": 1,
        "checks": 1,
        "segment_start_source_updates": 0,
        "segment_start_checks": 0,
        "last_check": last_check,
        "last_check_hash": stable_hash(last_check),
        "resumed_from_checkpoint_id": "",
        "resumable": True,
        "accepted": False,
        "model_owned_source": True,
        "runtime_edited_source": False,
        "proof_evidence_status": (
            "SCIENTIFIC_CODE_WORKSPACE_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    return {
        **body,
        "checkpoint_id": (
            "scientific_code_workspace_checkpoint:" + stable_hash(body)[:20]
        ),
    }


def test_scientific_progress_uses_same_owner_refs_and_stops_on_stagnation() -> None:
    question = OpenResearchQuestion(
        id="generic-progress",
        title="Generic progress",
        description="Continue one source from its exact execution observation.",
    )
    theory_packet_id = "theory:generic-progress"
    source_id = "estimator"
    checkpoint = _checkpoint(question_id=question.id, source_id=source_id)
    proposal = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": "algorithm-proposal:generic-progress",
        "scientific_source_transport": "native_client_tools",
    }
    row = {
        "estimator_id": source_id,
        "prototype_status": "FAILED",
        "smoke_passed": False,
        "scientific_code_workspace_failure": {
            "recovery_checkpoint": checkpoint,
            "runtime_edited_source": False,
        },
    }
    manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm-manifest:generic-progress",
        "question": {"id": question.id},
        "theory_packet_id": theory_packet_id,
        "llm_algorithm_engineer_proposal_id": proposal["packet_id"],
        "prototypes": [row],
    }
    task = AgentTask(
        task_id="algorithm:generic-progress",
        owner_subsystem="AlgorithmEngineer",
        objective="Implement the estimator.",
        inputs={
            "question": {"id": question.id},
            "theory_packet_id": theory_packet_id,
        },
        allowed_tools=("python", "filesystem_sandbox"),
        budget={"outer": {"remaining": 3}},
        expected_artifacts=("algorithm_sandbox_manifest",),
        acceptance_gate="source executes",
        stop_condition="accepted source or explicit blocker",
    )

    (
        next_task,
        evidence,
        observation,
        errors,
    ) = scientific_workspace_progress_continuation(
        task=task,
        question_id=question.id,
        manifest=manifest,
        proposal_packet=proposal,
        rows=[row],
        row_id_field="estimator_id",
        incomplete_source_ids=[source_id],
    )

    assert errors == []
    assert next_task is not None
    assert next_task.owner_subsystem == "AlgorithmEngineer"
    assert next_task.budget == task.budget
    assert "Architect" not in next_task.task_id
    assert observation is not None
    assert observation.payload["architect_routing_used"] is False
    assert evidence is not None
    assert evidence.status == "SCIENTIFIC_SOURCE_PROGRESS_RECORDED_NOT_ACCEPTED"
    progress_result = scientific_workspace_progress_result(
        task=task,
        source_owner="AlgorithmEngineer",
        produced_artifacts={},
        observations=(),
        tool_calls=(),
        evidence_entries=(evidence,),
        next_task=next_task,
        failure_classification="algorithm_source_workspace_progress_checkpoint",
    )
    marker = progress_result.next_task.budget[
        RUNTIME_CONTINUATION_BUDGET_MARKER_KEY
    ]
    assert marker["parent_task_id"] == task.task_id
    assert marker["next_task_id"] == next_task.task_id
    persisted_manifest = next_task.inputs[
        "scientific_code_workspace_progress_manifest"
    ]
    assert persisted_manifest["artifact_kind"] == (
        "RuntimeArtifactRef"
    )

    artifact_store = {
        manifest["manifest_id"]: manifest,
        proposal["packet_id"]: proposal,
    }
    blackboard = BlackboardState(
        project_id=question.id,
        artifacts=artifact_store,
    )
    hydrated_task = replace(
        next_task,
        inputs=resolve_runtime_artifact_references(
            next_task.inputs,
            artifact_store,
        ),
    )
    progress, load_errors = runtime_scientific_workspace_resume_plan(
        hydrated_task,
        blackboard,
        question_id=question.id,
        theory_packet_id=theory_packet_id,
        expected_manifest_kind="RuntimeAlgorithmSandboxManifest",
        proposal_id_field="llm_algorithm_engineer_proposal_id",
        row_id_field="estimator_id",
        expected_source_ids=[source_id],
        source_accepted=lambda candidate: candidate.get("smoke_passed") is True,
    )
    assert load_errors == []
    assert progress["checkpoints"][source_id] == checkpoint

    stagnant = scientific_workspace_progress_continuation(
        task=hydrated_task,
        question_id=question.id,
        manifest=manifest,
        proposal_packet=proposal,
        rows=[row],
        row_id_field="estimator_id",
        incomplete_source_ids=[source_id],
    )
    assert stagnant[0] is None
    assert any("no new executed progress" in error for error in stagnant[-1])


def test_direct_source_progress_resumes_without_a_planning_packet() -> None:
    question = OpenResearchQuestion(
        id="direct-source-progress",
        title="Direct source progress",
        description="Resume the source-owning model session.",
    )
    theory_packet_id = "theory:direct-source-progress"
    source_id = "estimator"
    checkpoint = _checkpoint(question_id=question.id, source_id=source_id)
    row = {
        "estimator_id": source_id,
        "prototype_status": "FAILED",
        "smoke_passed": False,
        "scientific_code_workspace_failure": {
            "recovery_checkpoint": checkpoint,
            "runtime_edited_source": False,
        },
    }
    manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm-manifest:direct-source-progress",
        "question": {"id": question.id},
        "theory_packet_id": theory_packet_id,
        "scientific_source_workspace_owns_planning": True,
        "scientific_source_workspace_intent_id": (
            "algorithm_source_workspace_intent:direct"
        ),
        "llm_algorithm_engineer_proposal_id": "",
        "prototypes": [row],
    }
    plan, errors = scientific_workspace_resume_plan(
        manifest=manifest,
        proposal_packet={},
        question_id=question.id,
        theory_packet_id=theory_packet_id,
        expected_manifest_kind="RuntimeAlgorithmSandboxManifest",
        proposal_id_field="llm_algorithm_engineer_proposal_id",
        row_id_field="estimator_id",
        expected_source_ids=[source_id],
        source_accepted=lambda candidate: candidate.get("smoke_passed") is True,
    )
    assert errors == []
    assert plan["source_workspace_owns_planning"] is True
    assert plan["source_workspace_intent_id"].endswith(":direct")
    task = AgentTask(
        task_id="algorithm:direct-source-progress",
        owner_subsystem="AlgorithmEngineer",
        objective="Continue the direct source workspace.",
        inputs={
            "question": {"id": question.id},
            "theory_packet_id": theory_packet_id,
        },
        budget={"outer": {"remaining": 3}},
    )
    next_task, _, _, continuation_errors = (
        scientific_workspace_progress_continuation(
            task=task,
            question_id=question.id,
            manifest=manifest,
            proposal_packet=None,
            rows=[row],
            row_id_field="estimator_id",
            incomplete_source_ids=[source_id],
        )
    )
    assert continuation_errors == []
    assert next_task is not None
    artifact_store = {manifest["manifest_id"]: manifest}
    hydrated = replace(
        next_task,
        inputs=resolve_runtime_artifact_references(
            next_task.inputs,
            artifact_store,
        ),
    )
    resumed, resume_errors = runtime_scientific_workspace_resume_plan(
        hydrated,
        BlackboardState(project_id=question.id, artifacts=artifact_store),
        question_id=question.id,
        theory_packet_id=theory_packet_id,
        expected_manifest_kind="RuntimeAlgorithmSandboxManifest",
        proposal_id_field="llm_algorithm_engineer_proposal_id",
        row_id_field="estimator_id",
        expected_source_ids=[source_id],
        source_accepted=lambda candidate: candidate.get("smoke_passed") is True,
    )
    assert resume_errors == []
    assert resumed["proposal_packet"] == {}
    assert resumed["checkpoints"][source_id] == checkpoint

    proposal = {"packet_id": "simulation-intent:bound"}
    simulation_manifest = {
        **manifest,
        "artifact_kind": "RuntimeSimulationManifest",
        "llm_simulation_engineer_proposal_id": proposal["packet_id"],
        "generated_simulation_sandbox_prototypes": [
            {**row, "simulation_id": source_id}
        ],
    }
    bound, bound_errors = scientific_workspace_resume_plan(
        manifest=simulation_manifest,
        proposal_packet=proposal,
        question_id=question.id,
        theory_packet_id=theory_packet_id,
        expected_manifest_kind="RuntimeSimulationManifest",
        proposal_id_field="llm_simulation_engineer_proposal_id",
        row_id_field="simulation_id",
        expected_source_ids=[source_id],
        source_accepted=lambda candidate: candidate.get("smoke_passed") is True,
    )
    assert bound_errors == []
    assert bound["proposal_packet"] == proposal
    _, stale_errors = scientific_workspace_resume_plan(
        manifest=simulation_manifest,
        proposal_packet={"packet_id": "simulation-intent:stale"},
        question_id=question.id,
        theory_packet_id=theory_packet_id,
        expected_manifest_kind="RuntimeSimulationManifest",
        proposal_id_field="llm_simulation_engineer_proposal_id",
        row_id_field="simulation_id",
        expected_source_ids=[source_id],
        source_accepted=lambda candidate: candidate.get("smoke_passed") is True,
    )
    assert "scientific workspace proposal packet is missing or stale" in stale_errors


def _research_context(question_id: str, theory_packet_id: str) -> dict:
    return {
        "architect_coordinator_proposal_id": "architect:generic-progress",
        "theory_packet_id": theory_packet_id,
        "empirical_evaluation_phase": (
            runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
        ),
        "architect_metric_protocol_gate": {
            "algorithm_execution_authorized": True,
            "confirmatory_simulation_authorized": False,
            "execution_authorized": False,
            "preflight_acceptance_id": "preflight:generic-progress",
        },
        "architect_runtime_plan": {
            "question_id": question_id,
            "evidence_contract": {
                "evaluation_mode": "capability_eval",
                "formal_verification_policy": "optional",
                "formal_required_for_final": False,
                "recommended_research_path": "empirical_first",
                "research_evaluation_requires_generated_algorithm_code": True,
                "research_evaluation_requires_generated_simulation_code": True,
            },
            "subsystem_execution_plan": [
                {"subsystem": "AlgorithmEngineer"},
                {"subsystem": "SimulationEvaluator"},
                {"subsystem": "CriticEvaluator"},
            ],
        },
    }


def test_algorithm_source_workspace_owns_planning_and_source(
    monkeypatch,
    tmp_path,
) -> None:
    question = OpenResearchQuestion(
        id="algorithm-direct-source",
        title="Direct algorithm source",
        description="Let one coding-agent session plan and implement an estimator.",
    )
    theory_packet_id = "theory:algorithm-direct-source"
    source_id = "estimator"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "estimator_specs": [
            {
                "id": source_id,
                "estimator_interface_contract": {
                    "request_fields": [
                        {
                            "name": "value",
                            "meaning": "Finite numeric input.",
                            "binding": "per_replicate_data",
                        }
                    ],
                    "response_fields": [
                        {
                            "name": "estimate",
                            "meaning": "Finite estimate.",
                            "normalization": "Identity scale.",
                            "derivation_ref": "C1",
                        }
                    ],
                },
            }
        ],
    }
    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("runtime must use the source workspace boundary")

    class SourceAgent:
        provider = Provider()
        proposal_calls = 0

        @staticmethod
        def source_workspace_owns_planning():
            return True

        @classmethod
        def propose(cls, **_kwargs):
            cls.proposal_calls += 1
            raise AssertionError("direct source planning must bypass propose()")

    source_calls = []

    def run_source_workspace(**kwargs):
        source_calls.append(kwargs)
        assert kwargs["source_deferred"] is True
        assert kwargs["code_draft"] == {"estimator_id": source_id}
        source = "model-owned source"
        return {
            "estimator_id": source_id,
            "prototype_status": "EXECUTED",
            "executor": "generated_python_sandbox",
            "source_code": source,
            "script_hash": stable_hash(source),
            "execution_attempted": True,
            "execution_smoke_passed": True,
            "smoke_passed": True,
            "scientific_code_workspace": {
                "artifact_id": f"{question.id}:{source_id}",
                "provider": "anthropic",
                "model": "claude-haiku-4-5-20251001",
                "model_tier": "haiku",
                "accepted": True,
                "model_owned_source": True,
                "runtime_edited_source": False,
                "transcript_fingerprint": "transcript:direct-source",
            },
        }, []

    monkeypatch.setattr(
        runtime_module,
        "_run_source_owner_scientific_workspace",
        run_source_workspace,
    )
    context = _research_context(question.id, theory_packet_id)
    deferred_task = AgentTask(
        task_id="simulation:evaluator-after-direct-source",
        owner_subsystem="SimulationEvaluator",
        objective="Author the executable evaluator after source review.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": context,
            "empirical_evaluation_phase": (
                runtime_module.EMPIRICAL_EVALUATION_PHASE_EXECUTABLE_EVALUATOR_AUTHORING
            ),
            "evaluator_source_authoring": True,
            "n_runs": 100_000,
            "seed": 7,
        },
    )
    result = runtime_module.AlgorithmEngineerRuntimeSubsystem(
        out_dir=tmp_path,
        n_runs=2,
        seed=7,
        proposal_agent=SourceAgent(),
        semantic_reviewer_available=False,
    ).run(
        AgentTask(
            task_id="algorithm:direct-source",
            owner_subsystem="AlgorithmEngineer",
            objective="Plan and implement the estimator in one source workspace.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "theory_packet_id": theory_packet_id,
                "architect_context": context,
                "implementation_gaps": [{"estimator_id": source_id}],
                "implementation_before_metric_freeze": True,
                "empirical_evaluation_phase": (
                    runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
                ),
                "deferred_metric_protocol_task": asdict(deferred_task),
                "n_runs": 2,
                "seed": 7,
            },
        ),
        BlackboardState(
            project_id=question.id,
            artifacts={theory_packet_id: theory_packet},
        ),
    )

    assert SourceAgent.proposal_calls == 0
    assert len(source_calls) == 1
    manifests = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
    ]
    assert len(manifests) == 1
    manifest = manifests[0]
    assert manifest["scientific_source_workspace_owns_planning"] is True
    assert manifest["planning_model_call_used"] is False
    assert manifest["n_passed"] == 1
    proposal_id = manifest["llm_algorithm_engineer_proposal_id"]
    review_packet = result.produced_artifacts[proposal_id]
    assert review_packet["source_workspace_planning_owned"] is True
    assert review_packet["planning_model_call_used"] is False
    assert review_packet["source_workspace_artifacts"][0]["source_hash"] == (
        stable_hash("model-owned source")
    )
    assert review_packet["theory_trace_alignment_contract"][
        "structured_alignment_observed"
    ] is False
    assert manifest["prototypes"][0]["source_llm_proposal_model_tier"] == (
        "haiku"
    )


def test_exploratory_simulation_source_workspace_owns_planning_and_source(
    monkeypatch,
    tmp_path,
) -> None:
    question = OpenResearchQuestion(
        id="simulation-direct-source",
        title="Direct exploratory simulation source",
        description=(
            "Let one coding-agent session design and execute a diagnostic simulation."
        ),
    )
    theory_packet_id = "theory:simulation-direct-source"
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "problem_card": {"estimand": "a generic scalar"},
        "estimator_specs": [],
        "theorem_cards": [],
    }

    class Provider:
        provider_name = "anthropic"
        calls = 0

        @classmethod
        def generate_client_tool_turn(cls, *_args, **_kwargs):
            cls.calls += 1
            raise AssertionError("runtime must use the source workspace boundary")

    provider = Provider()
    source_agent = LLMSimulationEngineerAgent(
        provider=provider,
        config=SimulationEngineerConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
        ),
    )

    source_calls = []

    def run_source_workspace(**kwargs):
        source_calls.append(kwargs)
        assert kwargs["source_deferred"] is True
        draft = dict(kwargs["code_draft"])
        simulation_id = str(draft["simulation_id"])
        assert draft["required_estimator_ids"] == []
        assert kwargs["workspace_context"]["source_workspace_planning_owned"] is True
        source = (
            "def run_sandbox(seed, replicates):\n"
            "    return {'diagnostic': float(replicates)}\n"
        )
        return {
            "simulation_id": simulation_id,
            "prototype_status": "EXECUTED",
            "executor": "generated_simulation_sandbox",
            "required_estimator_ids": [],
            "source_code": source,
            "script_hash": stable_hash(source),
            "execution_attempted": True,
            "execution_smoke_passed": True,
            "smoke_passed": True,
            "metrics": {"diagnostic": 2.0},
            "metric_contracts": [],
            "metric_contract_evaluation": {},
            "scientific_code_workspace": {
                "artifact_id": f"{question.id}:{simulation_id}",
                "provider": "anthropic",
                "model": "claude-haiku-4-5-20251001",
                "model_tier": "haiku",
                "accepted": True,
                "model_owned_source": True,
                "runtime_edited_source": False,
                "transcript_fingerprint": "transcript:direct-simulation-source",
            },
        }, []

    monkeypatch.setattr(
        runtime_module,
        "_run_source_owner_scientific_workspace",
        run_source_workspace,
    )
    context = _research_context(question.id, theory_packet_id)
    result = runtime_module.SimulationEvaluatorRuntimeSubsystem(
        proposal_agent=source_agent,
        sandbox_root=tmp_path,
        semantic_reviewer_available=False,
    ).run(
        AgentTask(
            task_id="simulation:direct-source",
            owner_subsystem="SimulationEvaluator",
            objective="Plan and execute one exploratory simulation workspace.",
            inputs={
                "question": runtime_module._question_to_payload(question),
                "theory_packet_id": theory_packet_id,
                "architect_context": context,
                "empirical_evaluation_phase": (
                    runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
                ),
                "n_runs": 2,
                "seed": 7,
            },
        ),
        BlackboardState(
            project_id=question.id,
            artifacts={theory_packet_id: theory_packet},
        ),
    )

    assert Provider.calls == 0
    assert len(source_calls) == 1
    manifests = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeSimulationManifest"
    ]
    assert len(manifests) == 1
    manifest = manifests[0]
    assert manifest["scientific_source_workspace_owns_planning"] is True
    assert manifest["planning_model_call_used"] is False
    assert manifest["n_exploratory_generated_simulation_sandbox_passed"] == 1
    proposal_id = manifest["llm_simulation_engineer_proposal_id"]
    review_packet = result.produced_artifacts[proposal_id]
    assert review_packet["source_workspace_planning_owned"] is True
    assert review_packet["planning_model_call_used"] is False
    assert review_packet["metric_contracts"] == []
    assert review_packet["source_workspace_intent_id"] == (
        manifest["scientific_source_workspace_intent_id"]
    )
    assert review_packet["simulation_code_drafts"][0]["simulation_id"] == (
        manifest["generated_simulation_sandbox_prototypes"][0]["simulation_id"]
    )
    assert manifest["generated_simulation_sandbox_prototypes"][0][
        "source_llm_proposal_model_tier"
    ] == "haiku"


def test_algorithm_subsystem_resumes_source_without_replanning(
    monkeypatch,
    tmp_path,
) -> None:
    question = OpenResearchQuestion(
        id="algorithm-progress",
        title="Algorithm progress",
        description="Resume one exact estimator source.",
    )
    theory_packet_id = "theory:algorithm-progress"
    source_id = "estimator"
    checkpoint = _checkpoint(question_id=question.id, source_id=source_id)
    proposal = {
        "artifact_kind": "AlgorithmEngineerProposalPacket",
        "packet_id": "algorithm-proposal:progress",
        "scientific_source_transport": "native_client_tools",
        "implementation_targets": [{"estimator_id": source_id}],
        "sandbox_code_drafts": [{"estimator_id": source_id}],
    }
    parent_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm-manifest:progress-parent",
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
        "llm_algorithm_engineer_proposal_id": proposal["packet_id"],
        "prototypes": [
            {
                "estimator_id": source_id,
                "prototype_status": "FAILED",
                "smoke_passed": False,
                "scientific_code_workspace_failure": {
                    "recovery_checkpoint": checkpoint,
                    "runtime_edited_source": False,
                },
            }
        ],
    }
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "estimator_specs": [
            {
                "id": source_id,
                "formula": "the model-owned estimator",
                "inputs": ["value"],
                "outputs": ["estimate"],
            }
        ],
    }
    accepted_source = (
        "def run_estimator(request):\n"
        "    return {'estimate': float(request.get('value', 0.0))}\n\n"
        "def run_sandbox(seed, replicates):\n"
        "    return {'estimate': 0.0}\n"
    )
    observed_sources: list[str] = []

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source workspace owns model turns")

    class SourceAgent:
        provider = Provider()
        proposal_calls = 0
        source_calls = 0

        @classmethod
        def propose(cls, **_kwargs):
            cls.proposal_calls += 1
            raise AssertionError("checkpoint continuation must bypass planning")

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            cls.source_calls += 1
            assert kwargs["recovery_checkpoint"] == checkpoint
            assert kwargs["code_draft"] == checkpoint["current_code_draft"]
            assert kwargs["initial_observation"] == checkpoint["last_check"]
            candidate = {
                **checkpoint["current_code_draft"],
                "code": accepted_source,
            }
            check = dict(kwargs["check_candidate"](candidate))
            return ScientificCodeWorkspaceResult(
                code_draft=candidate,
                check_result=check,
                evidence={
                    "artifact_id": f"{question.id}:{source_id}",
                    "workspace_operation": "initial_authoring",
                    "resumed_from_checkpoint_id": checkpoint["checkpoint_id"],
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "accepted": True,
                },
            )

    def execute_algorithm(**kwargs):
        source = str(kwargs["code_draft"]["code"])
        observed_sources.append(source)
        return (
            {
                "estimator_id": source_id,
                "prototype_status": "EXECUTED",
                "executor": "generated_python_sandbox",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "source_code": source,
                "script_hash": stable_hash(source),
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": True,
            },
            ToolCallRecord(
                tool_name="python.generated_algorithm_sandbox",
                exit_status="0",
            ),
        )

    monkeypatch.setattr(
        runtime_module,
        "_run_generated_code_sandbox",
        execute_algorithm,
    )
    context = _research_context(question.id, theory_packet_id)
    deferred_task = AgentTask(
        task_id="simulation:evaluator-after-algorithm-progress",
        owner_subsystem="SimulationEvaluator",
        objective="Author the executable evaluator after algorithm progress.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": context,
            "empirical_evaluation_phase": (
                runtime_module.EMPIRICAL_EVALUATION_PHASE_EXECUTABLE_EVALUATOR_AUTHORING
            ),
            "evaluator_source_authoring": True,
            "n_runs": 100_000,
            "seed": 7,
        },
    )
    task = AgentTask(
        task_id="algorithm-progress:resume",
        owner_subsystem="AlgorithmEngineer",
        objective="Resume the exact estimator source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": context,
            "implementation_gaps": [{"estimator_id": source_id}],
            "implementation_before_metric_freeze": True,
            "empirical_evaluation_phase": (
                runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            ),
            "deferred_metric_protocol_task": asdict(deferred_task),
            "scientific_code_workspace_progress_manifest": parent_manifest,
            "scientific_code_workspace_continuation_count": 1,
            "n_runs": 2,
            "seed": 7,
        },
    )
    result = runtime_module.AlgorithmEngineerRuntimeSubsystem(
        out_dir=tmp_path,
        n_runs=2,
        seed=7,
        proposal_agent=SourceAgent(),
        semantic_reviewer_available=False,
    ).run(
        task,
        BlackboardState(
            project_id=question.id,
            artifacts={
                theory_packet_id: theory_packet,
                proposal["packet_id"]: proposal,
                parent_manifest["manifest_id"]: parent_manifest,
            },
        ),
    )

    assert SourceAgent.proposal_calls == 0
    assert SourceAgent.source_calls == 1, (
        result.status,
        result.rationale,
        result.failure_classification,
        [observation.payload for observation in result.observations],
    )
    assert observed_sources == [accepted_source]
    manifests = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeAlgorithmSandboxManifest"
    ]
    assert len(manifests) == 1
    assert manifests[0]["n_passed"] == 1
    assert any(
        observation.observation_type == "algorithm_source_workspace_resumed"
        for observation in result.observations
    )


def test_simulation_subsystem_resumes_source_without_replanning(
    monkeypatch,
    tmp_path,
) -> None:
    question = OpenResearchQuestion(
        id="simulation-progress",
        title="Simulation progress",
        description="Resume one exact simulation source.",
    )
    theory_packet_id = "theory:simulation-progress"
    source_id = "simulation"
    checkpoint = _checkpoint(question_id=question.id, source_id=source_id)
    proposal = {
        "artifact_kind": "SimulationEngineerProposalPacket",
        "packet_id": "simulation-proposal:progress",
        "scientific_source_transport": "native_client_tools",
        "simulation_targets": [{"procedure_id": source_id}],
        "simulation_code_drafts": [
            {"simulation_id": source_id, "required_estimator_ids": []}
        ],
        "metric_contracts": [],
    }
    parent_manifest = {
        "schema_version": 1,
        "artifact_kind": "RuntimeSimulationManifest",
        "manifest_id": "simulation-manifest:progress-parent",
        "question": runtime_module._question_to_payload(question),
        "theory_packet_id": theory_packet_id,
        "llm_simulation_engineer_proposal_id": proposal["packet_id"],
        "generated_simulation_sandbox_prototypes": [
            {
                "simulation_id": source_id,
                "prototype_status": "FAILED",
                "smoke_passed": False,
                "scientific_code_workspace_failure": {
                    "recovery_checkpoint": checkpoint,
                    "runtime_edited_source": False,
                },
            }
        ],
    }
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_packet_id,
        "problem_card": {"estimand": "a generic scalar"},
        "estimator_specs": [],
        "theorem_cards": [],
    }
    accepted_source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'diagnostic': float(replicates)}\n"
    )
    observed_sources: list[str] = []

    class Provider:
        @staticmethod
        def generate_client_tool_turn(*_args, **_kwargs):
            raise AssertionError("the fake source workspace owns model turns")

    class SourceAgent:
        provider = Provider()
        proposal_calls = 0
        source_calls = 0

        @classmethod
        def propose(cls, **_kwargs):
            cls.proposal_calls += 1
            raise AssertionError("checkpoint continuation must bypass planning")

        @classmethod
        def iterate_code_with_tools(cls, **kwargs):
            cls.source_calls += 1
            assert kwargs["recovery_checkpoint"] == checkpoint
            candidate = {
                **checkpoint["current_code_draft"],
                "code": accepted_source,
            }
            check = dict(kwargs["check_candidate"](candidate))
            return ScientificCodeWorkspaceResult(
                code_draft=candidate,
                check_result=check,
                evidence={
                    "artifact_id": f"{question.id}:{source_id}",
                    "workspace_operation": "initial_authoring",
                    "resumed_from_checkpoint_id": checkpoint["checkpoint_id"],
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "accepted": True,
                },
            )

    def execute_simulation(**kwargs):
        source = str(kwargs["code_draft"]["code"])
        observed_sources.append(source)
        return (
            {
                "simulation_id": source_id,
                "prototype_status": "EXECUTED",
                "executor": "generated_simulation_sandbox",
                "language": "python",
                "requested_execution_profile": "stdlib",
                "executor_profile": "stdlib",
                "dependencies": [],
                "required_estimator_ids": [],
                "source_code": source,
                "script_hash": stable_hash(source),
                "execution_attempted": True,
                "execution_smoke_passed": True,
                "smoke_passed": True,
                "metrics": {"diagnostic": 2.0},
                "metric_contracts": [],
                "metric_contract_evaluation": {},
            },
            ToolCallRecord(
                tool_name="python.generated_simulation_sandbox",
                exit_status="0",
            ),
        )

    monkeypatch.setattr(
        runtime_module,
        "_run_generated_simulation_sandbox",
        execute_simulation,
    )
    context = _research_context(question.id, theory_packet_id)
    task = AgentTask(
        task_id="simulation-progress:resume",
        owner_subsystem="SimulationEvaluator",
        objective="Resume the exact simulation source.",
        inputs={
            "question": runtime_module._question_to_payload(question),
            "theory_packet_id": theory_packet_id,
            "architect_context": context,
            "empirical_evaluation_phase": (
                runtime_module.EMPIRICAL_EVALUATION_PHASE_EXPLORATORY
            ),
            "scientific_code_workspace_progress_manifest": parent_manifest,
            "scientific_code_workspace_continuation_count": 1,
            "n_runs": 2,
            "seed": 7,
        },
    )
    result = runtime_module.SimulationEvaluatorRuntimeSubsystem(
        proposal_agent=SourceAgent(),
        sandbox_root=tmp_path,
        semantic_reviewer_available=False,
    ).run(
        task,
        BlackboardState(
            project_id=question.id,
            artifacts={
                theory_packet_id: theory_packet,
                proposal["packet_id"]: proposal,
                parent_manifest["manifest_id"]: parent_manifest,
            },
        ),
    )

    assert SourceAgent.proposal_calls == 0
    assert SourceAgent.source_calls == 1
    assert observed_sources == [accepted_source]
    manifests = [
        artifact
        for artifact in result.produced_artifacts.values()
        if isinstance(artifact, dict)
        and artifact.get("artifact_kind") == "RuntimeSimulationManifest"
    ]
    assert len(manifests) == 1
    assert manifests[0]["n_exploratory_generated_simulation_sandbox_passed"] == 1, (
        result.status,
        result.rationale,
        result.failure_classification,
        manifests[0],
    )
    assert any(
        observation.observation_type == "simulation_source_workspace_resumed"
        for observation in result.observations
    )

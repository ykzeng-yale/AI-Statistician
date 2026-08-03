from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Mapping

from ai_statistician.agent_runtime import (
    AgentRuntime,
    AgentStepResult,
    AgentTask,
    BlackboardState,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.formalizer_llm import build_formalizer_prompt
from ai_statistician.model_backend import GeneratorRequest, GeneratorResponse
from ai_statistician.pseudo_formal_block_verifier_runtime_worker import (
    PSEUDO_FORMAL_BLOCK_VERIFIER_INDEPENDENCE_CONTRACT,
    PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_EXECUTION_KIND,
    PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_KIND,
    PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE,
    PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM,
    PseudoFormalBlockVerifierRuntimeWorker,
    pseudo_formal_block_verifier_feedback_task_errors,
)
from ai_statistician.research_paper_index import build_paper_source_index
from ai_statistician.pseudo_formal_block_verifier_worker import (
    pseudo_formal_block_verifier_request_rows,
    run_pseudo_formal_block_verifier_rows,
)
from ai_statistician.pseudo_formalization import (
    PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND,
    PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
    PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
    PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
    PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID,
    PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
)
from ai_statistician.research_agent_runtime import (
    FormalizationEvaluatorRuntimeSubsystem,
    ResearchAgentRuntimeConfig,
    _formalizer_proof_bank_runtime_memory_summary,
    _formalizer_pseudo_formal_work_order_rows,
    _runtime_pseudo_formal_block_verifier_dispatch_task,
    _runtime_pseudo_formal_block_verifier_work_order,
    _runtime_repeated_pseudo_formal_block_verifier_rows,
)
from ai_statistician.research_agent_runtime_audit import (
    _runtime_capability_scorecard,
    _runtime_typed_pseudo_formal_block_verifier_audit_summary,
)
from ai_statistician.research_schema import OpenResearchQuestion


class _PromptBoundVerifierBackend:
    provider_name = "static"

    def __init__(self, *, verdict: str = "accepted") -> None:
        self.verdict = verdict
        self.requests: list[GeneratorRequest] = []

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        self.requests.append(request)
        prompt = json.loads(request.user_prompt)
        payload = {
            "prompt_packet_id": prompt["prompt_packet_id"],
            "source_pseudo_formal_work_order_id": prompt[
                "source_pseudo_formal_work_order_id"
            ],
            "source_block_id": prompt["source_block_id"],
            "faithfulness_review": {
                "status": "faithful",
                "reason": "The bounded source anchor states the same rank argument.",
            },
            "block_verification": {
                "verdict": self.verdict,
                "reason": "The local argument follows from the explicit premise.",
                "verifier_provenance": "independent_block_verifier",
                "independent_verifier": True,
                "strictness_threshold": "strict",
                "aggregation_rule": "pessimistic_all_blocks_must_pass",
                "rollout_count": 1,
            },
            "cited_dependency_statement_ids": ["dep:exchangeability"],
            "issues": [],
            "proof_evidence_status": (
                "PSEUDO_FORMAL_BLOCK_VERIFIER_FEEDBACK_NOT_PROOF_EVIDENCE"
            ),
        }
        return GeneratorResponse(
            text=json.dumps(payload),
            provider=self.provider_name,
            model=request.model,
            metadata={"generator_only": True, "tools_available": False},
        )


class _FailingVerifierBackend:
    provider_name = "static"

    def __init__(self) -> None:
        self.requests: list[GeneratorRequest] = []

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        self.requests.append(request)
        raise RuntimeError("verifier provider unavailable")


def _request_row() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact_kind": "RuntimeLearningRow",
        "question_id": "generic_exchangeability",
        "learning_task": PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
        "pseudo_formal_method_contract_id": (
            PSEUDO_FORMAL_VERIFICATION_METHOD_CONTRACT_ID
        ),
        "pseudo_formal_pipeline_stage": PSEUDO_FORMAL_BLOCK_ROUTING_METHOD_STAGE,
        "target_theorem_name": "generic_rank_identity",
        "target_ids": ["generic_rank_identity", "block:rank"],
        "next_owner_subsystem": "BlockVerifier/CalibrationReferee",
        "source_pseudo_formal_work_order_id": "pf-work-order:rank",
        "source_formalizer_proposal_id": "formalizer-proposal:1",
        "source_formalization_manifest_id": "formalization-manifest:1",
        "source_packet_id": "pf-packet:1",
        "source_theorem_id": "generic_rank_identity",
        "source_block_id": "block:rank",
        "source_block_type": "lemma",
        "source_block_conclusion": "the rank has the claimed finite law",
        "block_depth": 1,
        "dependency_scope": "statement_only",
        "dependency_ids": ["dep:exchangeability"],
        "dependency_statement_context": [
            {
                "dependency_id": "dep:exchangeability",
                "statement": "the observations are exchangeable",
            }
        ],
        "scope_parent_id": "",
        "inherited_scope": ["finite sample"],
        "source_block_premises": ["the observations are exchangeable"],
        "source_block_proof_text": (
            "Permutation invariance makes every admissible rank equally likely."
        ),
        "source_anchors": [
            {
                "source_id": "paper:generic",
                "locator": "proof of the rank lemma",
                "excerpt": "exchangeability makes each admissible rank equally likely",
            }
        ],
        "independent_block_verification_required": True,
        "independent_block_verification_status": "pending",
        "row_kind": PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
        "target_lane": "formal_gap",
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": "PSEUDO_FORMALIZATION_NOT_PROOF_EVIDENCE",
        "input_summary": {
            "learning_task": PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK,
            "work_order_id": "pf-work-order:rank",
            "row_kind": PSEUDO_FORMAL_BLOCK_VERIFICATION_REQUEST_ROW_KIND,
            "source_block_id": "block:rank",
        },
    }


def test_formalizer_needs_review_root_reaches_independent_worker(
    tmp_path: Path,
) -> None:
    rows = _formalizer_pseudo_formal_work_order_rows(
        proposal_packet={
            "packet_id": "formalizer-proposal:review-root",
            "pseudo_formal_proof_packets": [
                {
                    "theorem_id": "generic_rank_identity",
                    "source_artifact_id": "theory:generic-rank",
                    "blocks": [
                        {
                            "block_id": "block:review-root",
                            "block_type": "theorem",
                            "premises": ["the observations are exchangeable"],
                            "conclusion": "the rank has the claimed finite law",
                            "proof_text": (
                                "Permutation invariance makes admissible ranks "
                                "equally likely."
                            ),
                            "dependency_ids": [],
                            "scope_parent_id": "",
                            "source_anchors": [
                                {
                                    "kind": "theory_trace",
                                    "id": "trace:rank-law",
                                    "excerpt": "exchangeability yields rank uniformity",
                                }
                            ],
                            "semantic_primitive_requirements": ["finite_rank_law"],
                            "lean_feasibility": "needs_semantic_definition",
                            "faithfulness_status": "needs_review",
                            "faithfulness_repair": {
                                "status": "needs_repair",
                                "attempts": 0,
                                "flagged_discrepancies": [],
                            },
                            "block_verification": {"verdict": "not_run"},
                        }
                    ],
                }
            ],
        }
    )

    request_rows = pseudo_formal_block_verifier_request_rows(rows)

    assert len(request_rows) == 1
    request_row = request_rows[0]
    assert request_row["row_kind"] == PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND
    assert request_row["learning_task"] == PSEUDO_FORMAL_BLOCK_ROUTING_LEARNING_TASK
    assert request_row["source_pseudo_formal_work_order_id"] == request_row["row_id"]
    assert request_row["dependency_statement_context"] == []

    backend = _PromptBoundVerifierBackend()
    turn = run_pseudo_formal_block_verifier_rows(
        request_rows,
        provider=backend,
        provider_name="static",
        model="static-haiku",
        model_tier="haiku",
        max_packets=1,
        question_id="generic_exchangeability",
        out_dir=tmp_path / "review_turn",
    )

    assert turn["all_ok"] is True
    assert turn["n_runtime_learning_rows"] == 1
    learning_row = turn["runtime_learning_rows"][0]
    assert learning_row["faithfulness_status"] == "faithful"
    assert learning_row["faithfulness_review"]["status"] == "faithful"
    assert learning_row["block_verification"]["verdict"] == "accepted"


def _runtime_fixture(
    tmp_path: Path,
    *,
    request_row: Mapping[str, Any] | None = None,
) -> tuple[
    PseudoFormalBlockVerifierRuntimeWorker,
    AgentTask,
    BlackboardState,
    _PromptBoundVerifierBackend,
]:
    question = {
        "id": "generic_exchangeability",
        "title": "Generic rank",
        "description": "Check a rank identity under exchangeability.",
    }
    row = dict(request_row) if isinstance(request_row, Mapping) else _request_row()
    source_manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization-manifest:1",
        "question": question,
        "pseudo_formal_work_order_rows": [row],
    }
    source_task = AgentTask(
        task_id="formalize:generic_exchangeability",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the generic theorem.",
        inputs={
            "question": question,
            "architect_context": {
                "runtime_learning_memory": {
                    "artifact_kind": "RuntimeLearningMemoryContext",
                    "source_paths": [],
                    "rows": [],
                    "counts": {"max_rows": 20},
                }
            },
        },
    )
    return_task = AgentTask(
        task_id="critic:generic_exchangeability",
        owner_subsystem="CriticEvaluator",
        objective="Review runtime evidence.",
        inputs={"question": question},
    )
    policy = {
        "provider_name": "static",
        "model": "",
        "model_tier": "haiku",
        "max_packets": 8,
        "max_tokens": 2000,
        "temperature": 0.0,
        "max_repair_attempts": 1,
        "independence_contract": (
            PSEUDO_FORMAL_BLOCK_VERIFIER_INDEPENDENCE_CONTRACT
        ),
    }
    work_order = {
        "schema_version": 1,
        "artifact_kind": PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_KIND,
        "work_order_id": "runtime-pf-bv-work-order:1",
        "question_id": question["id"],
        "target_subsystem": PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM,
        "source_formalization_manifest_id": source_manifest["manifest_id"],
        "source_formalization_manifest_hash": stable_hash(source_manifest),
        "work_order_rows": [row],
        "work_order_row_hashes": [stable_hash(row)],
        "execution_policy": policy,
        "execution_policy_fingerprint": stable_hash(policy),
        "source_task": asdict(source_task),
        "return_task": asdict(return_task),
        "kernel_verified": False,
        "source_theorem_kernel_verified": False,
        "proof_evidence_status": (
            PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_WORK_ORDER_NOT_PROOF_EVIDENCE
        ),
        "proof_evidence_boundary": PSEUDO_FORMALIZATION_PROOF_BOUNDARY,
    }
    backend = _PromptBoundVerifierBackend()
    worker = PseudoFormalBlockVerifierRuntimeWorker(
        out_root=tmp_path,
        source_rows_resolver=lambda manifest: [
            dict(value)
            for value in manifest.get("pseudo_formal_work_order_rows", []) or []
            if isinstance(value, Mapping)
        ],
        provider=backend,
        provider_name="static",
    )
    blackboard = BlackboardState(
        project_id="test",
        artifacts={
            source_manifest["manifest_id"]: source_manifest,
            work_order["work_order_id"]: work_order,
        },
    )
    task = AgentTask(
        task_id="pf-bv:generic_exchangeability",
        owner_subsystem=PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM,
        objective="Verify the bounded block.",
        inputs={
            "question": question,
            "pseudo_formal_block_verifier_work_order_id": work_order[
                "work_order_id"
            ],
            "pseudo_formal_block_verifier_work_order_hash": stable_hash(work_order),
        },
    )
    return worker, task, blackboard, backend


def test_in_memory_block_verifier_turn_emits_validated_nonproof_feedback(
    tmp_path: Path,
) -> None:
    backend = _PromptBoundVerifierBackend()

    manifest = run_pseudo_formal_block_verifier_rows(
        [_request_row()],
        provider=backend,
        provider_name="static",
        out_dir=tmp_path,
    )

    assert manifest["all_ok"] is True
    assert manifest["n_valid_responses"] == 1
    assert manifest["n_runtime_learning_rows"] == 1
    assert manifest["live_generator"] is False
    learning_row = manifest["runtime_learning_rows"][0]
    assert learning_row["question_id"] == "generic_exchangeability"
    assert learning_row["independent_block_verification_status"] == "completed"
    assert learning_row["faithfulness_status"] == "faithful"
    assert learning_row["faithfulness_review"]["status"] == "faithful"
    assert learning_row["block_verification"]["verdict"] == "accepted"
    assert learning_row["kernel_verified"] is False
    assert learning_row["source_theorem_kernel_verified"] is False
    assert backend.requests[0].metadata["subsystem"] == "PseudoFormalBlockVerifier"


def test_runtime_worker_returns_feedback_to_proofengineer_memory(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, backend = _runtime_fixture(tmp_path)

    result = worker.run(task, blackboard)

    assert result.status == "REVISE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ProofEngineer"
    blackboard.artifacts.update(result.produced_artifacts)
    assert pseudo_formal_block_verifier_feedback_task_errors(
        result.next_task,
        blackboard,
        question_id="generic_exchangeability",
    ) == []
    memory = result.next_task.inputs["architect_context"][
        "runtime_learning_memory"
    ]
    assert len(memory["rows"]) == 1
    assert memory["rows"][0]["question_id"] == "generic_exchangeability"
    assert memory["rows"][0]["block_verification"]["verdict"] == "accepted"
    execution = next(
        artifact
        for artifact in result.produced_artifacts.values()
        if artifact.get("artifact_kind")
        == PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_EXECUTION_KIND
    )
    assert execution["execution_contract_satisfied"] is True
    assert execution["capability_evidence_ok"] is False
    assert execution["kernel_verified"] is False
    contract = result.next_task.inputs[
        "pseudo_formal_block_verifier_feedback_contract"
    ]
    assert contract["runtime_work_order_id"] == task.inputs[
        "pseudo_formal_block_verifier_work_order_id"
    ]
    assert contract["runtime_turn_id"] in result.produced_artifacts
    assert contract["feedback_row_hashes"] == [stable_hash(memory["rows"][0])]
    assert contract["contract_fingerprint"] == execution[
        "feedback_contract_fingerprint"
    ]
    assert len(backend.requests) == 1


def test_faithfulness_review_feedback_reaches_real_formalizer_prompt(
    tmp_path: Path,
) -> None:
    review_row = _request_row()
    review_row["row_kind"] = PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND
    worker, task, blackboard, _backend = _runtime_fixture(
        tmp_path,
        request_row=review_row,
    )

    result = worker.run(task, blackboard)

    assert result.next_task is not None
    context = result.next_task.inputs["architect_context"]
    summary = _formalizer_proof_bank_runtime_memory_summary(
        context=context,
        proof_bank_obligation_catalog=[],
        theorem_goals=[],
        memory_kernel_verified_proof_obligation_ids=(),
        memory_prioritized_proof_obligation_ids=(),
    )
    assert summary[
        "pseudo_formal_independent_block_verification_feedback_active"
    ] is True
    assert summary[
        "pseudo_formal_independent_block_verification_verdicts"
    ] == ["accepted"]
    assert summary[
        "pseudo_formal_independent_block_verification_feedback_memory"
    ][0]["row_kind"] == PSEUDO_FORMAL_FAITHFULNESS_REVIEW_ROW_KIND
    assert len(
        _runtime_repeated_pseudo_formal_block_verifier_rows(
            [review_row],
            summary,
        )
    ) == 1
    revised_row = {
        **review_row,
        "source_block_proof_text": (
            review_row["source_block_proof_text"]
            + " The revised argument also checks the boundary rank."
        ),
    }
    assert _runtime_repeated_pseudo_formal_block_verifier_rows(
        [revised_row],
        summary,
    ) == []

    prompt = build_formalizer_prompt(
        question=OpenResearchQuestion(
            id="generic_exchangeability",
            title="Generic rank",
            description="Check a rank identity under exchangeability.",
        ),
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        registered_problem={},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary=summary,
        environment_feedback=result.next_task.inputs["environment_feedback"],
    )
    assert "Independent pseudo-formal block-verifier feedback is available" in prompt
    assert "RuntimePseudoFormalBlockVerifierFeedbackContract" in prompt
    assert "pseudo_formal_faithfulness_review" in prompt


def test_formalizer_rejects_tampered_pf_bv_parent_before_model_call(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _backend = _runtime_fixture(tmp_path)
    result = worker.run(task, blackboard)
    assert result.next_task is not None
    blackboard.artifacts.update(result.produced_artifacts)
    source_manifest_id = result.next_task.inputs[
        "pseudo_formal_block_verifier_feedback_contract"
    ]["source_formalization_manifest_id"]
    blackboard.artifacts[source_manifest_id] = {
        **blackboard.artifacts[source_manifest_id],
        "tampered": True,
    }

    class MustNotRunProposalAgent:
        def propose(self, **_kwargs: Any) -> Any:
            raise AssertionError("model must not run for invalid feedback lineage")

    outcome = FormalizationEvaluatorRuntimeSubsystem(
        proposal_agent=MustNotRunProposalAgent(),
    ).run(result.next_task, blackboard)

    assert outcome.status == "BLOCKED"
    assert outcome.failure_classification == (
        "pseudo_formal_block_verifier_feedback_binding_failed"
    )
    assert "source manifest hash mismatch" in outcome.observations[0].summary


def test_runtime_worker_routes_provider_failure_to_critic(tmp_path: Path) -> None:
    worker, task, blackboard, _backend = _runtime_fixture(tmp_path)
    failing_backend = _FailingVerifierBackend()
    worker.provider = failing_backend

    result = worker.run(task, blackboard)

    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "CriticEvaluator"
    feedback = result.next_task.inputs["pseudo_formal_block_verifier_feedback"]
    assert feedback["failure_classification"].endswith("contract_invalid")
    assert feedback["errors"] == [
        "RuntimeError: verifier provider unavailable"
    ]
    assert len(failing_backend.requests) == 1


def test_typed_runtime_executes_verifier_then_proofengineer_in_same_loop(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, backend = _runtime_fixture(tmp_path)

    class ProofEngineerProbe:
        name = "ProofEngineer"

        def run(
            self,
            proof_task: AgentTask,
            _blackboard: BlackboardState,
        ) -> AgentStepResult:
            feedback = proof_task.inputs["environment_feedback"]
            assert feedback[
                "pseudo_formal_independent_block_verification_feedback_active"
            ] is True
            assert feedback[
                "pseudo_formal_independent_block_verification_verdicts"
            ] == ["accepted"]
            return AgentStepResult(
                status="COMPLETED",
                rationale="ProofEngineer consumed the bounded verifier feedback.",
            )

    outcome = AgentRuntime(
        subsystems={
            PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM: worker,
            "ProofEngineer": ProofEngineerProbe(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)

    assert outcome.status == "COMPLETED"
    assert [trace.subsystem for trace in outcome.traces] == [
        PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM,
        "ProofEngineer",
    ]
    assert len(backend.requests) == 1


def _write_runtime_result(path: Path, outcome: Any) -> Path:
    path.write_text(json.dumps(outcome.to_json(), indent=2), encoding="utf-8")
    return path


def _scorecard_row(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return next(
        row
        for row in _runtime_capability_scorecard(payload)["rows"]
        if row["requirement_id"]
        == "typed_pseudo_formal_block_verifier_agent_runtime_feedback"
    )


def test_runtime_audit_requires_live_same_run_typed_feedback(tmp_path: Path) -> None:
    worker, task, blackboard, backend = _runtime_fixture(tmp_path)
    backend.provider_name = "anthropic"
    worker.provider_name = "anthropic"
    work_order_id = task.inputs["pseudo_formal_block_verifier_work_order_id"]
    work_order = blackboard.artifacts[work_order_id]
    work_order["execution_policy"]["provider_name"] = "anthropic"
    work_order["execution_policy_fingerprint"] = stable_hash(
        work_order["execution_policy"]
    )
    task = replace(
        task,
        inputs={
            **task.inputs,
            "pseudo_formal_block_verifier_work_order_hash": stable_hash(work_order),
        },
    )

    class ProofEngineerProbe:
        name = "ProofEngineer"

        def run(
            self,
            proof_task: AgentTask,
            _blackboard: BlackboardState,
        ) -> AgentStepResult:
            assert proof_task.inputs["environment_feedback"][
                "pseudo_formal_independent_block_verification_feedback_active"
            ] is True
            return AgentStepResult(
                status="COMPLETED",
                rationale="Consumed typed PF/BV feedback.",
            )

    outcome = AgentRuntime(
        subsystems={
            PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM: worker,
            "ProofEngineer": ProofEngineerProbe(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)
    result_path = _write_runtime_result(tmp_path / "live_result.json", outcome)
    errors: list[str] = []

    summary = _runtime_typed_pseudo_formal_block_verifier_audit_summary(
        result_paths=[result_path],
        errors=errors,
    )

    assert errors == []
    assert summary[
        "runtime_typed_pseudo_formal_block_verifier_contract_complete"
    ] is True
    assert summary[
        "runtime_typed_pseudo_formal_block_verifier_capability_evidence_complete"
    ] is True
    assert summary[
        "n_runtime_typed_pseudo_formal_block_verifier_live_executions"
    ] == 1
    assert summary[
        "n_runtime_typed_pseudo_formal_block_verifier_same_run_feedback_to_proofengineer"
    ] == 1
    assert _scorecard_row(summary)["passed"] is True


def test_runtime_audit_demotes_static_typed_feedback_from_capability_evidence(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _backend = _runtime_fixture(tmp_path)

    class ProofEngineerProbe:
        name = "ProofEngineer"

        def run(
            self,
            _task: AgentTask,
            _blackboard: BlackboardState,
        ) -> AgentStepResult:
            return AgentStepResult(status="COMPLETED", rationale="Consumed feedback.")

    outcome = AgentRuntime(
        subsystems={
            PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM: worker,
            "ProofEngineer": ProofEngineerProbe(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)
    result_path = _write_runtime_result(tmp_path / "static_result.json", outcome)

    summary = _runtime_typed_pseudo_formal_block_verifier_audit_summary(
        result_paths=[result_path],
        errors=[],
    )

    assert summary[
        "runtime_typed_pseudo_formal_block_verifier_contract_complete"
    ] is True
    assert summary[
        "runtime_typed_pseudo_formal_block_verifier_capability_evidence_complete"
    ] is False
    assert summary[
        "n_runtime_typed_pseudo_formal_block_verifier_static_or_fixture_executions"
    ] == 1
    assert _scorecard_row(summary)["passed"] is False


def test_runtime_audit_tracks_failed_verifier_feedback_to_critic_and_tampering(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, _backend = _runtime_fixture(tmp_path)
    worker.provider = _FailingVerifierBackend()

    class CriticProbe:
        name = "CriticEvaluator"

        def run(
            self,
            critic_task: AgentTask,
            _blackboard: BlackboardState,
        ) -> AgentStepResult:
            assert critic_task.inputs["pseudo_formal_block_verifier_feedback"][
                "failure_classification"
            ].endswith("contract_invalid")
            return AgentStepResult(
                status="COMPLETED",
                rationale="Consumed exact verifier diagnostics.",
            )

    outcome = AgentRuntime(
        subsystems={
            PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM: worker,
            "CriticEvaluator": CriticProbe(),
        },
        blackboard=blackboard,
    ).run(task, max_iterations=2)
    payload = outcome.to_json()
    result_path = tmp_path / "failed_result.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = _runtime_typed_pseudo_formal_block_verifier_audit_summary(
        result_paths=[result_path],
        errors=[],
    )

    assert summary[
        "runtime_typed_pseudo_formal_block_verifier_contract_complete"
    ] is True
    assert summary[
        "n_runtime_typed_pseudo_formal_block_verifier_same_run_feedback_to_critic"
    ] == 1
    execution = next(
        artifact
        for artifact in payload["blackboard"]["artifacts"].values()
        if artifact.get("artifact_kind")
        == PSEUDO_FORMAL_BLOCK_VERIFIER_RUNTIME_EXECUTION_KIND
    )
    execution["kernel_verified"] = True
    tampered_path = tmp_path / "tampered_result.json"
    tampered_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    tampered = _runtime_typed_pseudo_formal_block_verifier_audit_summary(
        result_paths=[tampered_path],
        errors=[],
    )

    assert tampered[
        "runtime_typed_pseudo_formal_block_verifier_contract_complete"
    ] is False
    assert any(
        "non-proof boundary mismatch" in issue
        for issue in tampered[
            "runtime_typed_pseudo_formal_block_verifier_contract_issues"
        ]
    )


def test_pseudo_formalization_sources_are_in_live_paper_index() -> None:
    urls = {record.url for record in build_paper_source_index()}

    assert "https://arxiv.org/abs/2605.20531" in urls
    assert "https://github.com/Slim205/pseudo-formalization" in urls


def test_runtime_worker_replays_without_a_second_model_call(tmp_path: Path) -> None:
    worker, task, blackboard, backend = _runtime_fixture(tmp_path)
    first = worker.run(task, blackboard)
    blackboard.artifacts.update(first.produced_artifacts)

    replay = worker.run(task, blackboard)

    assert replay.status == "REVISE"
    assert replay.next_task == first.next_task
    assert len(backend.requests) == 1
    assert replay.observations[0].observation_type.endswith("execution_replay")


def test_runtime_worker_rejects_changed_work_order_before_model_call(
    tmp_path: Path,
) -> None:
    worker, task, blackboard, backend = _runtime_fixture(tmp_path)
    work_order_id = task.inputs["pseudo_formal_block_verifier_work_order_id"]
    blackboard.artifacts[work_order_id]["question_id"] = "other-question"

    result = worker.run(task, blackboard)

    assert result.status == "BLOCKED"
    assert result.failure_classification.endswith("work_order_invalid")
    assert backend.requests == []


def test_formalizer_dispatch_builds_hash_bound_runtime_work_order() -> None:
    question = OpenResearchQuestion(
        id="generic_exchangeability",
        title="Generic rank",
        description="Check a rank identity under exchangeability.",
    )
    source_task = AgentTask(
        task_id="formalize:generic_exchangeability",
        owner_subsystem="FormalizationEvaluator",
        objective="Formalize the theorem.",
        inputs={"question": asdict(question)},
    )
    return_task = AgentTask(
        task_id="critic:generic_exchangeability",
        owner_subsystem="CriticEvaluator",
        objective="Review runtime evidence.",
        inputs={"question": asdict(question)},
    )
    manifest = {
        "artifact_kind": "RuntimeFormalizationManifest",
        "manifest_id": "formalization-manifest:dispatch",
        "pseudo_formal_work_order_rows": [_request_row()],
    }
    config = ResearchAgentRuntimeConfig(
        pseudo_formal_block_verifier_runtime=True,
        pseudo_formal_block_verifier_runtime_max_packets=4,
    )

    work_order = _runtime_pseudo_formal_block_verifier_work_order(
        source_task=source_task,
        question=question,
        architect_context={},
        formalization_manifest=manifest,
        return_task=return_task,
        runtime_config=config,
        provider_name="static",
        model="",
    )
    dispatch = _runtime_pseudo_formal_block_verifier_dispatch_task(
        question=question,
        architect_context={},
        work_order=work_order,
    )

    assert work_order["target_subsystem"] == PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM
    assert work_order["source_formalization_manifest_hash"] == stable_hash(manifest)
    assert work_order["work_order_row_hashes"] == [stable_hash(_request_row())]
    assert work_order["execution_policy"]["max_packets"] == 4
    assert work_order["execution_policy"]["model_tier"] == "haiku"
    assert work_order["kernel_verified"] is False
    assert dispatch.owner_subsystem == PSEUDO_FORMAL_BLOCK_VERIFIER_SUBSYSTEM
    assert dispatch.inputs["pseudo_formal_block_verifier_work_order_hash"] == (
        stable_hash(work_order)
    )

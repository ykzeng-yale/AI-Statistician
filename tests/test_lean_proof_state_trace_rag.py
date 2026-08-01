from __future__ import annotations

import json
from pathlib import Path

import ai_statistician.formalizer_llm as formalizer_module
import ai_statistician.research_agent_runtime as runtime_module
from ai_statistician.agent_runtime import AgentTask
from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceRetriever,
)
from ai_statistician.huggingface_lean_source_audit import (
    PINNED_HF_LEAN_DATASETS,
)
from ai_statistician.lean_proof_state_trace_rag import (
    LeanProofStateTraceRetriever,
    ai4slt_proof_state_trace_rag_descriptor,
    attach_ai4slt_proof_state_trace_rag,
    discover_ai4slt_proof_state_trace_retriever,
)
from ai_statistician.research_schema import OpenResearchQuestion


def test_ai4slt_trace_dataset_is_in_shared_source_inventory() -> None:
    assert "yuanhezhang/lean4-stat-learning-theory-novel" in (
        PINNED_HF_LEAN_DATASETS
    )


def _write_trace_fixture(path: Path) -> Path:
    rows = [
        {
            "file_path": "SLT/Gaussian/Concentration.lean",
            "full_name": "gaussian_lipschitz_tail",
            "theorem_statement": (
                "theorem gaussian_lipschitz_tail "
                "(hL : LipschitzWith L f) : tailBound f X t"
            ),
            "traced_tactics": [
                {
                    "state_before": (
                        "f : E -> Real\n"
                        "hL : LipschitzWith L f\n"
                        "⊢ tailBound f X t"
                    ),
                    "tactic": "apply concentration_of_mgf_bound",
                    "state_after": "⊢ mgfBound f X t",
                    "annotated_tactic_provenances": [
                        {
                            "full_name": "SLT.concentration_of_mgf_bound",
                            "def_path": "SLT/Gaussian/Concentration.lean",
                        }
                    ],
                },
                {
                    "state_before": "⊢ mgfBound f X t",
                    "tactic": "exact gaussian_mgf_bound hL",
                    "state_after": "no goals",
                    "annotated_tactic_provenances": [],
                },
            ],
        },
        {
            "file_path": "SLT/LeastSquares/Basic.lean",
            "full_name": "leastSquares_excessRisk",
            "theorem_statement": (
                "theorem leastSquares_excessRisk : excessRisk betaHat <= rate"
            ),
            "traced_tactics": [
                {
                    "state_before": (
                        "betaHat : Fin d -> Real\n"
                        "⊢ excessRisk betaHat <= rate"
                    ),
                    "tactic": "apply basic_inequality",
                    "state_after": "⊢ empiricalProcessTerm betaHat <= rate",
                    "annotated_tactic_provenances": [],
                }
            ],
        },
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _write_module_alignment_trace_fixture(path: Path) -> Path:
    rows = [
        {
            "file_path": "SLT/Unrelated/Bridge.lean",
            "full_name": "Axioms.generic_bound",
            "theorem_statement": "theorem generic_bound : bound x",
            "traced_tactics": [
                {
                    "state_before": "x : Real\n⊢ bound x",
                    "tactic": "exact generic_bound_of_nonneg x",
                    "state_after": "no goals",
                    "annotated_tactic_provenances": [],
                }
            ],
        },
        {
            "file_path": "SLT/LeastSquares/Target.lean",
            "full_name": "LeastSquares.localized_bound",
            "theorem_statement": "theorem localized_bound : bound x",
            "traced_tactics": [
                {
                    "state_before": "x : Real\n⊢ bound x",
                    "tactic": "exact localized_bound_of_basic_inequality x",
                    "state_after": "no goals",
                    "annotated_tactic_provenances": [],
                }
            ],
        },
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _trace_retriever(path: Path) -> LeanProofStateTraceRetriever:
    return LeanProofStateTraceRetriever(
        path,
        index_path=path.with_suffix(".sqlite"),
        source_id="fixture_traces",
        dataset_id="fixture/dataset",
        dataset_revision="fixture-revision",
        split="novel/train",
        toolchain="lean-fixture",
        mathlib_revision="mathlib-fixture",
        expected_sha256="",
    )


def _formal_source_retriever() -> FormalSourceRetriever:
    return FormalSourceRetriever(
        [
            FormalDeclaration(
                source_id="lean_stat_learning_theory",
                source_type="lean_library",
                path="SLT/Gaussian/Concentration.lean",
                line=41,
                kind="theorem",
                name="SLT.concentration_of_mgf_bound",
                namespace="SLT",
                signature=(
                    "theorem concentration_of_mgf_bound "
                    "(h : mgfBound f X t) : tailBound f X t"
                ),
                reference=(
                    "Boucheron-Lugosi-Massart (2013), Theorem 2.1"
                ),
            )
        ]
    )


def test_trace_index_searches_states_and_preserves_provenance(
    tmp_path: Path,
) -> None:
    provider = _trace_retriever(
        _write_trace_fixture(tmp_path / "novel-train.jsonl")
    )

    hits = provider.search(
        "LipschitzWith tailBound concentration",
        k=2,
        source_scope_ids=("lean_stat_learning_theory",),
    )

    assert hits
    assert hits[0].theorem_name == "gaussian_lipschitz_tail"
    assert hits[0].tactic == "apply concentration_of_mgf_bound"
    assert hits[0].premise_provenance == (
        {
            "full_name": "SLT.concentration_of_mgf_bound",
            "def_path": "SLT/Gaussian/Concentration.lean",
        },
    )
    health = provider.health_report(refresh=True)
    assert health["all_ok"]
    assert health["n_theorems"] == 2
    assert health["n_trace_steps"] == 3
    assert health["n_steps_with_premise_provenance"] == 1

    descriptor = ai4slt_proof_state_trace_rag_descriptor(
        trace_retriever=provider
    )
    assert descriptor["available"] is True
    assert descriptor["dataset_id"] == "fixture/dataset"
    assert descriptor["split"] == "novel/train"
    assert descriptor["health"]["n_trace_steps"] == 3
    assert "trace_path" not in descriptor["health"]
    assert "index_path" not in descriptor["health"]
    assert "current Lean goal" in descriptor["activation_policy"]
    assert descriptor["proof_evidence_status"] == (
        "PROOF_STATE_TRACE_RETRIEVAL_TOPOLOGY_NOT_PROOF_EVIDENCE"
    )


def test_trace_search_uses_declaration_module_as_a_soft_ranking_prior(
    tmp_path: Path,
) -> None:
    provider = _trace_retriever(
        _write_module_alignment_trace_fixture(tmp_path / "module-traces.jsonl")
    )

    baseline = provider.search("x : Real bound x", k=2)
    aligned = provider.search(
        "x : Real bound x",
        k=2,
        preferred_modules=("SLT.LeastSquares.Target",),
    )

    assert baseline[0].theorem_name == "Axioms.generic_bound"
    assert aligned[0].theorem_name == "LeastSquares.localized_bound"
    assert aligned[0].base_score > 0
    assert aligned[0].declaration_alignment_bonus > 0
    assert aligned[0].declaration_alignment_bonus <= (
        0.2 * aligned[0].base_score
    )
    assert aligned[0].declaration_alignment_signals == ("EXACT_SOURCE_MODULE",)


def test_trace_retrieval_is_source_scoped_and_checksum_guarded(
    tmp_path: Path,
) -> None:
    path = _write_trace_fixture(tmp_path / "novel-train.jsonl")
    provider = _trace_retriever(path)

    assert provider.search(
        "excessRisk betaHat",
        source_scope_ids=("unrelated_formal_source",),
    ) == []
    assert provider.search(
        "excessRisk betaHat",
        source_scope_ids=("ai4slt_companion_premise_corpus",),
    )

    mismatched = LeanProofStateTraceRetriever(
        path,
        index_path=tmp_path / "mismatched.sqlite",
        expected_sha256="0" * 64,
    )
    assert not mismatched.ensure_index()
    assert mismatched.search("excessRisk betaHat") == []


def test_trace_auto_discovery_has_an_explicit_ablation_switch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = _write_trace_fixture(tmp_path / "novel-train.jsonl")
    provider = _trace_retriever(path)
    attached = attach_ai4slt_proof_state_trace_rag(
        {
            "compiler_feedback": {
                "stderr": "betaHat excessRisk basic inequality"
            }
        },
        trace_retriever=provider,
    )
    assert "proof_state_trace_rag" in attached
    monkeypatch.setenv(
        "AI_STATISTICIAN_AI4SLT_PROOF_STATE_TRACES",
        str(path),
    )
    monkeypatch.setenv(
        "AI_STATISTICIAN_AI4SLT_PROOF_STATE_TRACE_ENABLED",
        "false",
    )

    assert discover_ai4slt_proof_state_trace_retriever() is None
    assert "proof_state_trace_rag" not in (
        attach_ai4slt_proof_state_trace_rag(attached)
    )


def test_trace_context_requires_live_proof_state_and_is_non_evidence(
    tmp_path: Path,
) -> None:
    provider = _trace_retriever(
        _write_trace_fixture(tmp_path / "novel-train.jsonl")
    )

    class LoadedComposite:
        def __init__(self) -> None:
            self.providers = (_formal_source_retriever(),)
            self.search_calls = 0

        def search(self, _query: str, *, k: int = 10):
            self.search_calls += 1
            raise AssertionError(
                "trace premise binding must not fan out provider searches"
            )

    formal_sources = LoadedComposite()
    semantic_only = attach_ai4slt_proof_state_trace_rag(
        {
            "retrieval_query_seeds": [
                "Lipschitz Gaussian concentration theorem"
            ]
        },
        trace_retriever=provider,
    )
    assert "proof_state_trace_rag" not in semantic_only

    attached = attach_ai4slt_proof_state_trace_rag(
        {
            "target_lean_declaration": (
                "Gaussian.gaussian_lipschitz_tail"
            ),
            "compiler_feedback": {
                "stderr": (
                    "application type mismatch while proving "
                    "LipschitzWith tailBound concentration"
                )
            },
            "residual_goal_excerpt": [
                "hL : LipschitzWith L f\n⊢ tailBound f X t"
            ],
            "retrieval_query_seeds": ["Gaussian concentration"],
            "formal_source_scope_ids": ["lean_stat_learning_theory"],
            "formal_source_grounding_hits": [
                {
                    "query_role": "semantic_target",
                    "hits": [
                        {
                            "source_id": "lean_stat_learning_theory",
                            "name": "gaussian_lipschitz_tail",
                            "namespace": "Gaussian",
                            "path": "SLT/Gaussian/Concentration.lean",
                            "declaration_source_context": {
                                "module": "SLT.Gaussian.Concentration"
                            },
                        },
                        {
                            "source_id": "unrelated_formal_source",
                            "name": "Unrelated.lookalike",
                            "namespace": "Unrelated",
                            "path": "Other/Lookalike.lean",
                        },
                    ],
                }
            ],
        },
        formal_source_retriever=formal_sources,
        trace_retriever=provider,
    )

    trace_context = attached["proof_state_trace_rag"]
    assert trace_context["n_hits"] >= 1
    assert trace_context["declaration_rag_anchors"] == {
        "source_ids": ["lean_stat_learning_theory"],
        "theorem_names": ["gaussian_lipschitz_tail"],
        "modules": ["SLT.Gaussian.Concentration"],
    }
    assert trace_context["n_declaration_aligned_hits"] >= 1
    assert "EXACT_SOURCE_THEOREM_NAME" in trace_context["hits"][0][
        "declaration_rag_alignment"
    ]["signals"]
    assert trace_context["hits"][0]["declaration_rag_alignment"][
        "authority"
    ].endswith("NOT_TACTIC_OR_PROOF_AUTHORITY")
    assert len(trace_context["trace_sha256"]) == 64
    assert trace_context["n_target_name_overlap_hits"] == 1
    assert trace_context["hits"][0]["target_name_overlap"] == (
        "EXACT_SHORT_NAME_OVERLAP"
    )
    assert "held-out generalization" in trace_context[
        "evaluation_contamination_policy"
    ]
    assert trace_context["proof_evidence_status"] == (
        "PROOF_STATE_TRACE_RETRIEVAL_CONTEXT_NOT_PROOF_EVIDENCE"
    )
    assert "kernel_verified" not in json.dumps(trace_context).lower()
    first_premise = trace_context["hits"][0]["premise_provenance"][0]
    assert first_premise["current_resolution_status"] == (
        "CURRENT_FORMAL_SOURCE_INDEX_EXACT_NAME_AND_PATH"
    )
    assert "concentration_of_mgf_bound" in first_premise["current_signature"]
    assert formal_sources.search_calls == 0
    assert "ai4slt_proof_state_trace_rag" in attached[
        "available_runtime_tools"
    ]

    repeated = attach_ai4slt_proof_state_trace_rag(
        attached,
        formal_source_retriever=formal_sources,
        trace_retriever=provider,
    )
    assert repeated["proof_state_trace_rag"]["query_fingerprint"] == (
        trace_context["query_fingerprint"]
    )

    refreshed = attach_ai4slt_proof_state_trace_rag(
        {
            **attached,
            "target_lean_declaration": "LeastSquares.leastSquares_excessRisk",
            "compiler_feedback": {
                "stderr": (
                    "betaHat : Fin d -> Real\n"
                    "⊢ excessRisk betaHat <= rate"
                )
            },
            "residual_goal_excerpt": [
                "betaHat : Fin d -> Real\n⊢ excessRisk betaHat <= rate"
            ],
            "retrieval_query_seeds": [
                "leastSquares excessRisk basic inequality"
            ],
            "formal_source_grounding_hits": [
                {
                    "query_role": "semantic_target",
                    "hits": [
                        {
                            "source_id": "lean_stat_learning_theory",
                            "name": "leastSquares_excessRisk",
                            "namespace": "LeastSquares",
                            "path": "SLT/LeastSquares/Basic.lean",
                            "declaration_source_context": {
                                "module": "SLT.LeastSquares.Basic"
                            },
                        }
                    ],
                }
            ],
        },
        formal_source_retriever=formal_sources,
        trace_retriever=provider,
    )
    assert refreshed["proof_state_trace_rag"]["query_fingerprint"] != (
        trace_context["query_fingerprint"]
    )
    assert refreshed["proof_state_trace_rag"]["hits"][0][
        "source_theorem_name"
    ] == "leastSquares_excessRisk"
    assert refreshed["proof_state_trace_rag"]["declaration_rag_anchors"][
        "modules"
    ] == ["SLT.LeastSquares.Basic"]

    no_match = attach_ai4slt_proof_state_trace_rag(
        {
            **attached,
            "compiler_feedback": {"stderr": "zzzzuniquezzzz"},
            "residual_goal_excerpt": [],
            "retrieval_query_seeds": [],
        },
        formal_source_retriever=formal_sources,
        trace_retriever=provider,
    )
    assert "proof_state_trace_rag" not in no_match


def test_runtime_and_external_search_carry_trace_context(
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    def attach_fixture(context, *, formal_source_retriever=None):
        calls.append(
            {
                "context": dict(context),
                "formal_source_retriever": formal_source_retriever,
            }
        )
        return {
            **dict(context),
            "proof_state_trace_rag": {
                "provider": "fixture_trace_provider",
                "proof_evidence_status": (
                    "PROOF_STATE_TRACE_RETRIEVAL_CONTEXT_NOT_PROOF_EVIDENCE"
                ),
                "hits": [{"state_before": "⊢ p", "tactic": "exact hp"}],
            },
        }

    monkeypatch.setattr(
        runtime_module,
        "attach_ai4slt_proof_state_trace_rag",
        attach_fixture,
    )
    grounded = (
        runtime_module._proofengineer_repair_context_with_formal_source_grounding(
            {
                "target_lean_declaration": "exact_source",
                "target_theorem_statement": (
                    "theorem exact_source (p : Prop) (hp : p) : p"
                ),
                "compiler_feedback": {
                    "diagnostics": ["unsolved goals\n⊢ p"]
                },
            }
        )
    )

    assert calls
    assert grounded["proof_state_trace_rag"]["provider"] == (
        "fixture_trace_provider"
    )

    question = OpenResearchQuestion(
        "trace_context_fixture",
        "Trace context fixture",
        "Check typed proof-search transport.",
        (),
    )
    request = runtime_module._runtime_external_proof_search_request(
        task=AgentTask(
            task_id="proofengineer:trace-context",
            owner_subsystem="ProofEngineer",
            objective="repair exact source theorem",
            inputs={},
        ),
        question=question,
        environment_feedback={
            "proofengineer_repair_context": grounded,
        },
    )

    assert request["proof_state_trace_rag"] == grounded[
        "proof_state_trace_rag"
    ]


def test_formalizer_compaction_preserves_bounded_trace_states() -> None:
    state = "h : p\n" + "local context\n" * 80 + "⊢ p"
    compact = formalizer_module._compact_value(
        {
            "context_kind": "exact_source_theorem_whole_proof_repair",
            "proof_state_trace_rag": {
                "provider": "fixture_trace_provider",
                "declaration_rag_anchors": {
                    "source_ids": ["lean_stat_learning_theory"],
                    "theorem_names": ["prior"],
                    "modules": ["SLT.Prior"],
                },
                "n_declaration_aligned_hits": 1,
                "hits": [
                    {
                        "source_theorem_statement": "theorem prior : p",
                        "state_before": state,
                        "tactic": "exact h",
                        "state_after": "no goals",
                        "candidate_status": (
                            "ANALOGICAL_STATE_ACTION_REQUIRES_"
                            "CURRENT_PROJECT_REVALIDATION"
                        ),
                    }
                ],
                "proof_evidence_status": (
                    "PROOF_STATE_TRACE_RETRIEVAL_CONTEXT_NOT_PROOF_EVIDENCE"
                ),
            },
        }
    )

    trace = compact["proof_state_trace_rag"]
    assert trace["provider"] == "fixture_trace_provider"
    assert trace["declaration_rag_anchors"]["modules"] == ["SLT.Prior"]
    assert trace["n_declaration_aligned_hits"] == 1
    assert trace["hits"][0]["state_before"] == state
    assert trace["proof_evidence_status"].endswith(
        "NOT_PROOF_EVIDENCE"
    )

    instructions = formalizer_module._formalizer_mode_specific_instructions(
        {},
        {
            "repair_owner_agent": "ProofEngineer",
            "proofengineer_repair_context": {
                "proof_state_trace_rag": trace,
            },
        },
    )
    trace_instruction = next(
        row
        for row in instructions
        if "AI4SLT proof-state transitions" in row
    )
    assert "analogies" in trace_instruction
    assert "rerun the exact current artifact" in trace_instruction

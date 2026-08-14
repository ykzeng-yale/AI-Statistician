from __future__ import annotations

from copy import deepcopy
import hashlib
import json

from ai_statistician.critic_evaluator_llm import (
    CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
    build_critic_canonical_evidence_view,
    build_critic_evaluator_prompt,
    validate_critic_evaluator_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.research_source_library import load_research_source_snapshot
from ai_statistician.theory_workspace import theory_workspace_document_manifest


def _critic_packet() -> dict[str, object]:
    return {
        "current_observation_assessment": {
            "observed_status": "FAILURE_OBSERVED",
            "observed_failure": "Two artifacts state incompatible target identities.",
            "evidence_refs": ["artifact:a", "artifact:b"],
            "causal_hypotheses": [],
            "independent_missing_evidence": [],
        },
        "coordination_assessment": {
            "scope": "cross_workspace",
            "conflicting_artifact_ids": ["artifact:a", "artifact:b"],
            "rationale": "The exact target identities differ.",
        },
        "evidence_boundary_audit": [
            {
                "artifact_id": "artifact:a",
                "evidence_type": "theory",
                "boundary_ok": True,
                "observed_claim": "target a",
                "authority_boundary": "proposal",
                "boundary_observation": "not proof",
            }
        ],
        "critic_findings": [
            {
                "critic": "independent",
                "finding": "Artifact identities conflict.",
                "evidence_refs": ["artifact:a", "artifact:b"],
                "uncertainty": "low",
            }
        ],
        "dimension_assessments": [
            {
                "dimension": "theory",
                "status": "CONTRADICTED",
                "evidence_refs": ["artifact:a", "artifact:b"],
                "rationale": "The target identities conflict.",
                "gaps": ["Resolve the target identity."],
            },
            {
                "dimension": "scientific_code",
                "status": "SUPPORTED",
                "evidence_refs": ["artifact:a"],
                "rationale": "The code evidence is internally bound.",
                "gaps": [],
            },
            {
                "dimension": "empirical",
                "status": "SUPPORTED",
                "evidence_refs": ["artifact:b"],
                "rationale": "The empirical evidence is internally bound.",
                "gaps": [],
            },
            {
                "dimension": "formal",
                "status": "NOT_REQUESTED",
                "evidence_refs": [],
                "rationale": "Formal verification was not requested.",
                "gaps": [],
            },
        ],
        "gap_disclosure": {
            "status": "COMPLETE",
            "disclosed_gaps": ["The target identity conflict is unresolved."],
            "evidence_refs": ["artifact:a", "artifact:b"],
            "rationale": "All observed gaps are disclosed.",
        },
        "research_disposition": {
            "status": "REJECT",
            "blocking_dimensions": ["theory"],
            "rationale": "The theory target is contradicted.",
        },
        "proof_evidence_status": CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
        "kernel_verified": False,
        "full_frontier_theorem_proved": False,
    }


def test_cross_workspace_scope_requires_two_exact_artifact_ids() -> None:
    packet = _critic_packet()
    assert validate_critic_evaluator_packet(packet) == []

    packet["coordination_assessment"] = {
        "scope": "cross_workspace",
        "conflicting_artifact_ids": ["artifact:a"],
        "rationale": "Several lanes failed.",
    }

    assert (
        "cross_workspace coordination requires at least two distinct exact "
        "conflicting_artifact_ids"
    ) in validate_critic_evaluator_packet(packet)


def test_critic_can_accept_without_inventing_a_finding() -> None:
    packet = _critic_packet()
    packet["current_observation_assessment"] = {
        "observed_status": "NO_BLOCKING_FAILURE",
        "observed_failure": "",
        "evidence_refs": ["canonical:view"],
        "causal_hypotheses": [],
        "independent_missing_evidence": [],
    }
    packet["coordination_assessment"] = {
        "scope": "none",
        "conflicting_artifact_ids": [],
        "rationale": "No incompatible artifact claims were observed.",
    }
    packet["critic_findings"] = []
    dimensions = deepcopy(packet["dimension_assessments"])
    for row in dimensions:
        if row["dimension"] in {"theory", "scientific_code", "empirical"}:
            row["status"] = "SUPPORTED"
            row["gaps"] = []
    packet["dimension_assessments"] = dimensions
    packet["gap_disclosure"] = {
        "status": "COMPLETE",
        "disclosed_gaps": [],
        "evidence_refs": ["canonical:view"],
        "rationale": "No unresolved gap is supported by the final evidence view.",
    }
    packet["research_disposition"] = {
        "status": "ACCEPT",
        "blocking_dimensions": [],
        "rationale": "All requested research dimensions are supported.",
    }

    assert validate_critic_evaluator_packet(packet) == []

    packet["dimension_assessments"][0]["status"] = "INCONCLUSIVE"
    assert (
        "ACCEPT requires supported required dimensions, correctly marked "
        "not-applicable dimensions, no contradicted dimension, complete gap "
        "disclosure, and no blocking dimensions"
    ) in validate_critic_evaluator_packet(packet)


def test_canonical_evidence_view_excludes_legacy_simulation_flags() -> None:
    view = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet={
            "artifact_kind": "TheoryDerivationPacket",
            "packet_id": "theory:1",
            "serious_theory_mode": True,
        },
        algorithm_manifest={
            "artifact_kind": "RuntimeAlgorithmSandboxManifest",
            "manifest_id": "algorithm:1",
            "theory_packet_id": "theory:1",
            "n_live_generated_code_executed": 1,
            "n_passed": 1,
        },
        simulation_manifest={
            "artifact_kind": "RuntimeSimulationManifest",
            "manifest_id": "simulation:1",
            "theory_packet_id": "theory:1",
            "generated_simulation_passed": True,
            "simulation_passed": True,
            "exploratory_simulation_passed": False,
            "registered_simulation_passed": False,
            "registered_procedures": ["legacy-only"],
            "generated_simulation_sandbox_prototypes": [
                {
                    "simulation_id": "simulation-source:1",
                    "smoke_passed": True,
                    "metrics": {"coverage": 0.95},
                    "metric_contract_evaluation": {
                        "metric_requirement_set_id": "metric-set:1",
                        "n_contracts": 1,
                        "n_passed": 1,
                        "n_failed": 0,
                        "all_required_passed": True,
                    },
                }
            ],
        },
        formalization_manifest={},
        artifacts={},
        formal_verification_policy="optional",
    )

    serialized = str(view)
    assert "legacy-only" not in serialized
    assert view["dimension_requirements"] == {
        "theory": "optional",
        "scientific_code": "optional",
        "empirical": "optional",
        "formal": "optional",
    }
    assert view["empirical"]["generated_simulation_passed"] is True
    assert view["empirical"]["prototypes"][0]["reported_metrics"] == {
        "coverage": 0.95
    }


def test_canonical_evidence_view_hydrates_authoritative_theory_documents(
    tmp_path,
) -> None:
    source_root = tmp_path / "sources"
    source_root.mkdir()
    source_text = (
        "# Published premise\n"
        "Assume finite variance.\n"
        "Then the normalized estimator has the stated limiting variance.\n"
    )
    source_path = source_root / "paper.md"
    source_path.write_text(source_text, encoding="utf-8")
    source_manifest_path = tmp_path / "source-manifest.json"
    source_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "snapshot_id": "published-sources",
                "source_horizon": "2025-12-31",
                "source_root": "sources",
                "documents": [
                    {
                        "document_id": "paper-1",
                        "title": "Published premise",
                        "source_kind": "paper",
                        "relative_path": "paper.md",
                        "sha256": hashlib.sha256(
                            source_text.encode("utf-8")
                        ).hexdigest(),
                        "model_visible": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    research_sources = load_research_source_snapshot(source_manifest_path)
    exact_source = research_sources.read(
        "paper-1", line_start=2, line_end=3
    )
    documents = {
        "derivations/main.md": (
            "# Claim\n\nA model-authored derivation grounded in "
            f"`{exact_source['citation_ref']}`.\n"
        )
    }
    workspace = tmp_path / "theory"
    target = workspace / "derivations/main.md"
    target.parent.mkdir(parents=True)
    target.write_text(documents["derivations/main.md"])
    packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:file-backed",
        "serious_theory_mode": True,
        "theory_workspace_manifest": theory_workspace_document_manifest(
            documents,
            workspace_dir=workspace,
        ),
        "llm_client_tool_loop": {
            "research_source_snapshot": {
                "snapshot_id": "published-sources",
                "snapshot_hash": research_sources.snapshot_hash,
            },
            "source_search_refs": [
                {"query_hash": "query-hash", "hits": []}
            ],
            "source_read_refs": [
                {
                    "snapshot_id": research_sources.snapshot_id,
                    "snapshot_hash": research_sources.snapshot_hash,
                    "document_id": "paper-1",
                    "document_sha256": exact_source["sha256"],
                    "line_start": 2,
                    "line_end": 3,
                    "content_sha256": exact_source["content_sha256"],
                    "citation_ref": exact_source["citation_ref"],
                }
            ],
        },
    }

    view = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet=packet,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={"theory:file-backed": packet},
        formal_verification_policy="optional",
        research_sources=research_sources,
    )

    assert view["theory"]["authoritative_documents_loaded"] is True
    assert view["theory"]["authoritative_documents"] == [
        {
            "path": "derivations/main.md",
            "sha256": view["theory"]["documents"][0]["sha256"],
            "content": documents["derivations/main.md"],
        }
    ]
    assert view["theory"]["research_source_grounding"]["snapshot"] == {
        "snapshot_id": "published-sources",
        "snapshot_hash": research_sources.snapshot_hash,
    }
    assert view["theory"]["research_source_grounding"]["read_refs"][0][
        "document_id"
    ] == "paper-1"
    cited_sources = view["theory"]["research_source_grounding"][
        "cited_source_observations"
    ]
    assert cited_sources["cited_ref_count"] == 1
    assert cited_sources["resolved_exact_source_count"] == 1
    assert cited_sources["observations"][0]["status"] == (
        "RESOLVED_EXACT_SOURCE"
    )
    assert cited_sources["observations"][0]["content"] == "\n".join(
        source_text.splitlines()[1:3]
    )
    assert view["theory"]["research_source_grounding"]["runtime_audit"] == {
        "snapshot_hash": research_sources.snapshot_hash,
        "author_read_ref_count": 1,
        "cited_ref_count": 1,
        "resolved_exact_source_count": 1,
        "unresolved_cited_ref_count": 0,
        "source_text_persisted": False,
    }

    detached_packet = deepcopy(packet)
    detached_workspace = detached_packet.pop("llm_client_tool_loop")
    detached_workspace.update(
        {
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "artifact_id": "theory-workspace-evidence:file-backed",
            "runtime_source_theory_packet_id": detached_packet["packet_id"],
            "runtime_source_theory_packet_hash": stable_hash(detached_packet),
        }
    )
    detached_view = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet=detached_packet,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={
            detached_packet["packet_id"]: detached_packet,
            detached_workspace["artifact_id"]: detached_workspace,
        },
        formal_verification_policy="optional",
        research_sources=research_sources,
    )
    assert detached_view["theory"]["research_source_grounding"][
        "cited_source_observations"
    ] == cited_sources
    assert detached_view["theory"]["research_source_grounding"][
        "workspace_evidence"
    ]["artifact_id"] == detached_workspace["artifact_id"]

    prompt = build_critic_evaluator_prompt(
        question=OpenResearchQuestion(
            id="generic",
            title="Generic source audit",
            description="Audit one cited mathematical premise.",
        ),
        retrieval_manifest={},
        theory_packet=packet,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        canonical_evidence_view=view,
    )
    assert "Assume finite variance" in prompt
    assert exact_source["citation_ref"] in prompt

    tampered_packet = deepcopy(packet)
    tampered_packet["llm_client_tool_loop"]["source_read_refs"][0][
        "content_sha256"
    ] = "0" * 64
    tampered_view = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet=tampered_packet,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={"theory:file-backed": tampered_packet},
        formal_verification_policy="optional",
        research_sources=research_sources,
    )
    tampered_sources = tampered_view["theory"]["research_source_grounding"][
        "cited_source_observations"
    ]
    assert tampered_sources["resolved_exact_source_count"] == 0
    assert tampered_sources["unresolved_cited_ref_count"] == 1
    assert tampered_sources["observations"][0]["status"] == (
        "SOURCE_RANGE_IDENTITY_MISMATCH"
    )
    assert tampered_sources["observations"][0]["content"] == ""

    uncited_documents = {
        "derivations/main.md": "# Claim\n\nNo source citation is asserted here.\n"
    }
    target.write_text(uncited_documents["derivations/main.md"], encoding="utf-8")
    uncited_packet = deepcopy(packet)
    uncited_packet["theory_workspace_manifest"] = (
        theory_workspace_document_manifest(
            uncited_documents,
            workspace_dir=workspace,
        )
    )
    uncited_view = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet=uncited_packet,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={"theory:file-backed": uncited_packet},
        formal_verification_policy="optional",
        research_sources=research_sources,
    )
    assert uncited_view["theory"]["research_source_grounding"][
        "cited_source_observations"
    ]["cited_ref_count"] == 0
    assert "Assume finite variance" not in str(uncited_view)


def test_canonical_evidence_view_uses_task_intent_for_required_dimensions() -> None:
    view = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet={"packet_id": "theory:1"},
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={},
        formal_verification_policy="optional",
        evidence_contract={
            "evaluation_mode": "research_eval",
            "research_evaluation_requires_generated_algorithm_code": True,
            "research_evaluation_requires_generated_simulation_code": True,
            "dimension_requirements": {"formal": "not_applicable"},
        },
    )

    assert view["dimension_requirements"] == {
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
    }


def test_critic_prompt_references_large_workspace_artifacts_without_copying_them() -> None:
    repeated_source = "UNIQUE_FULL_SOURCE_SENTINEL\n" * 50_000
    theory_packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:large",
        "theorem_cards": [{"derivation": repeated_source}],
        "ok": True,
    }
    algorithm_manifest = {
        "artifact_kind": "RuntimeAlgorithmSandboxManifest",
        "manifest_id": "algorithm:large",
        "theory_packet_id": "theory:large",
        "n_executed": 2,
        "n_passed": 2,
        "prototypes": [{"source": repeated_source}],
    }
    current_observation = {
        "feedback_id": "observation:current",
        "failure_classification": "formalizer_workspace_exhausted",
        "raw_stderr": "exact current diagnostic",
    }
    canonical_view = {
        "artifact_kind": "CriticCanonicalEvidenceView",
        "theory": {"artifact_id": "theory:large", "content_hash": "theory-hash"},
        "scientific_code": {
            "artifact_id": "algorithm:large",
            "content_hash": "algorithm-hash",
        },
    }

    prompt = build_critic_evaluator_prompt(
        question=OpenResearchQuestion(
            id="large-critic-context",
            title="Audit a large workspace",
            description="Keep final audit context reference-driven.",
        ),
        retrieval_manifest={"manifest_id": "retrieval:large"},
        theory_packet=theory_packet,
        simulation_manifest={"manifest_id": "simulation:large"},
        algorithm_manifest=algorithm_manifest,
        formalization_manifest={
            "manifest_id": "formalization:large",
            "counts": {"formal_gap": 1, "kernel_verified": 0},
        },
        canonical_evidence_view=canonical_view,
        environment_feedback=current_observation,
    )

    assert len(prompt) < 30_000
    assert "UNIQUE_FULL_SOURCE_SENTINEL" not in prompt
    assert '"artifact_id":"theory:large"' in prompt
    assert '"artifact_id":"algorithm:large"' in prompt
    assert '"content_hash"' in prompt
    assert '"raw_stderr":"exact current diagnostic"' in prompt

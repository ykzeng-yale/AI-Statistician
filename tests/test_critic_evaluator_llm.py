from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re

import pytest

from ai_statistician.critic_evaluator_llm import (
    CRITIC_EVALUATION_SUBMIT_TOOL,
    CRITIC_EVIDENCE_READ_TOOL,
    CRITIC_EVIDENCE_SEARCH_TOOL,
    CRITIC_EVALUATOR_JSON_SCHEMA,
    CRITIC_EVALUATOR_PROPOSAL_NOT_EVIDENCE,
    CRITIC_GAP_DISCLOSURE_COMPLETE,
    CRITIC_SOURCE_RESULT_INSPECT_TOOL,
    CRITIC_SOURCE_RESULT_READ_TOOL,
    CriticEvaluatorConfig,
    LLMCriticEvaluatorAgent,
    build_critic_canonical_evidence_view,
    build_critic_evaluator_prompt,
    critic_required_dimension_evidence_gaps,
    source_replication_evidence_view,
    validate_critic_evaluator_packet,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolTurnResponse,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.research_source_library import load_research_source_snapshot
from ai_statistician.packet_validation import PacketValidationError
from ai_statistician.theory_revision_lineage import (
    build_theory_claim_revision_delta,
)
from ai_statistician.theory_workspace import (
    THEORY_MODEL_REASONING_CONTRACT,
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    theory_workspace_document_manifest,
)


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
                "dimension": "source_replication",
                "status": "NOT_REQUESTED",
                "evidence_refs": [],
                "rationale": "Source replication was not requested.",
                "gaps": [],
            },
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


def _critic_submission() -> dict[str, object]:
    packet = _critic_packet()
    for field in (
        "proof_evidence_status",
        "kernel_verified",
        "full_frontier_theorem_proved",
    ):
        packet.pop(field)
    return packet


def _source_result_critic_fixture(tmp_path):
    question_id = "critic-source-result-inspection"
    output_dir = tmp_path / "source-output"
    workspace = output_dir / "source_workspace"
    workspace.mkdir(parents=True)
    csv_content = "method,error\nreference,0.125\n"
    pdf_content = b"%PDF-1.4\n% exact critic figure\n%%EOF\n"
    (workspace / "results.csv").write_text(csv_content, encoding="utf-8")
    (workspace / "figure.pdf").write_bytes(pdf_content)
    manifest_path = output_dir / "source_replication_manifest.json"
    manifest_body = {
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": "source_replication:critic-results",
        "question_id": question_id,
        "runtime_generated": True,
        "model_authored": False,
        "runtime_edited_source": False,
        "command_owned_by_model": False,
        "execution_status": "EXECUTED",
        "manifest_path": str(manifest_path),
        "result_artifacts": [
            {
                "relative_path": "results.csv",
                "sha256": hashlib.sha256(csv_content.encode()).hexdigest(),
                "size_bytes": len(csv_content.encode()),
                "content_encoding": "utf-8",
                "text_line_count": 2,
            },
            {
                "relative_path": "figure.pdf",
                "sha256": hashlib.sha256(pdf_content).hexdigest(),
                "size_bytes": len(pdf_content),
                "content_encoding": "binary_not_embedded",
            },
        ],
        "execution_streams": [],
        "proof_evidence_status": (
            "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    manifest = {**manifest_body, "manifest_hash": stable_hash(manifest_body)}
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    canonical_view = {
        "artifact_kind": "CriticCanonicalEvidenceView",
        "question_id": question_id,
        "view_hash": "critic-source-result-view",
        "dimension_requirements": {
            "source_replication": "required",
            "theory": "required",
            "scientific_code": "required",
            "empirical": "required",
            "formal": "not_applicable",
        },
        "required_dimension_evidence_gaps": [],
        "source_replication": {
            "present": True,
            "lineage_verified": True,
            "source_execution": {
                "present": True,
                "lineage_verified": True,
                "artifact_id": manifest["artifact_id"],
                "manifest_hash": manifest["manifest_hash"],
                "execution_status": manifest["execution_status"],
            },
        },
    }
    submission = _critic_submission()
    source_assessment = next(
        row
        for row in submission["dimension_assessments"]
        if row["dimension"] == "source_replication"
    )
    source_assessment.update(
        {
            "status": "SUPPORTED",
            "evidence_refs": [manifest["artifact_id"]],
            "rationale": "The exact selected result was inspected.",
            "gaps": [],
        }
    )
    return question_id, manifest, canonical_view, submission, csv_content


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


def test_nonaccept_disposition_requires_complete_explicit_gap_disclosure() -> None:
    packet = _critic_packet()
    packet["gap_disclosure"]["status"] = "INCOMPLETE"

    errors = validate_critic_evaluator_packet(packet)
    assert (
        "gap_disclosure status must be COMPLETE after disclosing all known gaps; "
        "COMPLETE does not mean research success"
    ) in errors

    packet = _critic_packet()
    packet["gap_disclosure"]["disclosed_gaps"] = []
    packet["gap_disclosure"]["evidence_refs"] = []
    next(
        row
        for row in packet["dimension_assessments"]
        if row["dimension"] == "theory"
    )["gaps"] = []
    errors = validate_critic_evaluator_packet(packet)
    assert "non-ACCEPT disposition requires at least one disclosed gap" in errors
    assert "non-ACCEPT disposition requires gap disclosure evidence_refs" in errors
    assert "blocking dimensions require explicit dimension gaps: theory" in errors


def test_gap_disclosure_tool_schema_and_validator_share_one_enum() -> None:
    assert CRITIC_EVALUATOR_JSON_SCHEMA["properties"]["gap_disclosure"][
        "properties"
    ]["status"]["enum"] == [CRITIC_GAP_DISCLOSURE_COMPLETE]
    assert validate_critic_evaluator_packet(_critic_packet()) == []


def test_critic_tool_schema_is_the_only_structured_output_contract() -> None:
    prompt = build_critic_evaluator_prompt(
        question=OpenResearchQuestion(
            id="critic-single-contract",
            title="Use one Critic tool contract",
            description="Keep the final review ABI in one schema.",
        ),
        retrieval_manifest={},
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        formalization_manifest={},
        canonical_evidence_view={"view_hash": "critic-view"},
        client_tool_submission=True,
    )

    assert CRITIC_EVALUATOR_JSON_SCHEMA["additionalProperties"] is False
    assert "coordination_assessment" in CRITIC_EVALUATOR_JSON_SCHEMA["required"]
    assert CRITIC_EVALUATOR_JSON_SCHEMA["properties"][
        "current_observation_assessment"
    ]["additionalProperties"] is False
    dimensions = CRITIC_EVALUATOR_JSON_SCHEMA["properties"][
        "dimension_assessments"
    ]
    assert dimensions["minItems"] == dimensions["maxItems"] == 5
    assert "maxItems" not in CRITIC_EVALUATOR_JSON_SCHEMA["properties"][
        "critic_findings"
    ]
    assert "maxItems" not in CRITIC_EVALUATOR_JSON_SCHEMA["properties"][
        "current_observation_assessment"
    ]["properties"]["causal_hypotheses"]
    assert "required_output_contract" not in prompt
    assert "at most 3 causal hypotheses" not in prompt
    assert "5 audit or finding rows" not in prompt

    packet = _critic_packet()
    packet.pop("coordination_assessment")
    assert "missing or empty field: coordination_assessment" in (
        validate_critic_evaluator_packet(packet)
    )


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

    next(
        row
        for row in packet["dimension_assessments"]
        if row["dimension"] == "theory"
    )["status"] = "INCONCLUSIVE"
    errors = validate_critic_evaluator_packet(packet)
    mismatch = next(error for error in errors if error.startswith("ACCEPT evidence mismatch:"))
    assert '"theory":"INCONCLUSIVE"' in mismatch


def test_critic_cannot_accept_with_runtime_derived_required_evidence_gap() -> None:
    packet = _critic_packet()
    packet["current_observation_assessment"] = {
        "observed_status": "INCONCLUSIVE",
        "observed_failure": "",
        "evidence_refs": ["canonical:view/empirical"],
        "causal_hypotheses": [],
        "independent_missing_evidence": [
            "The required executable evaluator output is invalid."
        ],
    }
    packet["coordination_assessment"] = {
        "scope": "none",
        "conflicting_artifact_ids": [],
        "rationale": "This is one missing evidence item, not a conflict.",
    }
    packet["critic_findings"] = []
    for row in packet["dimension_assessments"]:
        if row["dimension"] in {"theory", "scientific_code", "empirical"}:
            row["status"] = "SUPPORTED"
            row["gaps"] = []
    packet["gap_disclosure"] = {
        "status": "COMPLETE",
        "disclosed_gaps": [
            "The required executable evaluator output is invalid."
        ],
        "evidence_refs": ["canonical:view/required_dimension_evidence_gaps"],
        "rationale": "The runtime-derived evidence deficit is disclosed.",
    }
    packet["research_disposition"] = {
        "status": "ACCEPT",
        "blocking_dimensions": [],
        "rationale": "All dimension rows were marked supported.",
    }
    required_dimension_evidence_gaps = [
        "empirical.executable_evaluator_authority_output_invalid"
    ]

    errors = validate_critic_evaluator_packet(
        packet,
        required_dimension_evidence_gaps=required_dimension_evidence_gaps,
    )
    mismatch = next(
        error for error in errors if error.startswith("ACCEPT evidence mismatch:")
    )
    assert "empirical.executable_evaluator_authority_output_invalid" in mismatch


def test_supported_dimension_cannot_disclose_an_unresolved_gap() -> None:
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
    for row in packet["dimension_assessments"]:
        if row["dimension"] in {"theory", "scientific_code", "empirical"}:
            row["status"] = "SUPPORTED"
            row["gaps"] = []
    scientific_code = next(
        row
        for row in packet["dimension_assessments"]
        if row["dimension"] == "scientific_code"
    )
    scientific_code["gaps"] = [
        "The required executable implementation is not yet available."
    ]
    packet["gap_disclosure"] = {
        "status": "COMPLETE",
        "disclosed_gaps": list(scientific_code["gaps"]),
        "evidence_refs": ["canonical:view/scientific_code"],
        "rationale": "All known gaps are disclosed.",
    }
    packet["research_disposition"] = {
        "status": "ACCEPT",
        "blocking_dimensions": [],
        "rationale": "All required dimensions are supported.",
    }

    errors = validate_critic_evaluator_packet(packet)

    assert (
        "dimension_assessments[2] SUPPORTED cannot contain unresolved gaps"
        in errors
    )


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
        "source_replication": "optional",
        "theory": "optional",
        "scientific_code": "optional",
        "empirical": "optional",
        "formal": "optional",
    }
    assert view["empirical"]["generated_simulation_passed"] is True
    assert view["empirical"]["prototypes"][0]["reported_metrics"] == {
        "coverage": 0.95
    }


def test_canonical_evidence_view_exposes_preflight_report_and_scratch_failures(
    tmp_path,
) -> None:
    report_content = "# Independent report\n\nAll symbolic checks passed.\n"
    report_path = tmp_path / "review.md"
    report_path.write_text(report_content, encoding="utf-8")
    theory = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:1",
        "serious_theory_mode": True,
    }
    preflight = {
        "artifact_kind": "ArchitectTheoryExecutionPreflightReviewPacket",
        "packet_id": "preflight:1",
        "overall_verdict": "ACCEPT",
        "findings": [],
        "review_report": {
            "artifact_kind": "TheoryExecutionPreflightReviewDocument",
            "document_id": "theory_preflight_review_document:1",
            "path": str(report_path),
            "persisted": True,
            "sha256": hashlib.sha256(report_content.encode("utf-8")).hexdigest(),
            "byte_size": len(report_content.encode("utf-8")),
        },
        "preflight_scratch_execution_refs": [
            {
                "scratch_run": 1,
                "status": "REJECTED_CONTRACT",
                "execution_attempted": False,
                "returncode": -1,
                "request_hash": "request-hash",
                "result_hash": "",
                "errors": ["generated source must define run_sandbox"],
            }
        ],
    }
    acceptance = {
        "artifact_kind": "RuntimeArchitectTheoryExecutionPreflightAcceptance",
        "acceptance_id": "acceptance:1",
        "source_theory_packet_id": "theory:1",
        "preflight_packet_id": "preflight:1",
    }
    view = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet=theory,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={
            "theory:1": theory,
            "preflight:1": preflight,
            "acceptance:1": acceptance,
        },
        formal_verification_policy="optional",
    )

    independent = view["theory"]["independent_preflight"]
    assert independent["review_report"]["content_loaded"] is True
    assert independent["review_report"]["content"] == report_content
    assert independent["review_report"]["load_error"] == ""
    assert independent["scratch_observation_summary"] == {
        "run_count": 1,
        "successful_execution_count": 0,
        "non_success_count": 1,
        "status_counts": {"REJECTED_CONTRACT": 1},
        "boundary": (
            "Runtime-projected raw execution status; exploratory scratch is "
            "not theory or proof evidence and a failure is not automatically "
            "a mathematical blocker."
        ),
    }
    assert independent["scratch_observations"][0]["errors"] == [
        "generated source must define run_sandbox"
    ]

    prompt = build_critic_evaluator_prompt(
        question=OpenResearchQuestion(
            id="generic",
            title="Generic theory audit",
            description="Audit a mathematical derivation.",
        ),
        retrieval_manifest={},
        theory_packet=theory,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        canonical_evidence_view=view,
    )
    assert "Never call a rejected, failed, unavailable, or hash-mismatched" in prompt
    assert "never use preflight ACCEPT" in prompt
    assert "outside the claim index" in prompt
    assert prompt.count(THEORY_MODEL_REASONING_CONTRACT) == 1
    assert "exact definitions and stated assumptions" in prompt
    assert "each tool call encodes the proposition" in prompt
    assert "correct conclusion does not validate" in prompt
    assert "required_dimension_evidence_gaps is a runtime-derived" in prompt
    assert "terminal validator will return any mismatch" in prompt
    assert "All symbolic checks passed" in prompt
    assert "REJECTED_CONTRACT" in prompt

    report_path.write_text("tampered", encoding="utf-8")
    tampered = build_critic_canonical_evidence_view(
        question_id="generic",
        theory_packet=theory,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={
            "theory:1": theory,
            "preflight:1": preflight,
            "acceptance:1": acceptance,
        },
        formal_verification_policy="optional",
    )["theory"]["independent_preflight"]["review_report"]
    assert tampered["content_loaded"] is False
    assert tampered["content"] == ""
    assert tampered["load_error"] == "sha256_mismatch,byte_size_mismatch"


def test_canonical_evidence_view_resolves_successful_referee_probe(
    tmp_path,
) -> None:
    source = (
        "def run_sandbox(seed, replicates):\n"
        "    return {'only_checked': 'easy_positive_case'}\n"
    )
    metrics = {"only_checked": "easy_positive_case", "passed": True}
    source_path = tmp_path / "scratch.py"
    result_path = tmp_path / "scratch.json"
    source_path.write_text(source, encoding="utf-8")
    result_path.write_text(json.dumps(metrics), encoding="utf-8")
    theory = {"packet_id": "theory:probe"}
    preflight = {
        "artifact_kind": "ArchitectTheoryExecutionPreflightReviewPacket",
        "packet_id": "preflight:probe",
        "preflight_scratch_execution_refs": [
            {
                "scratch_run": 1,
                "status": "EXECUTED",
                "execution_attempted": True,
                "returncode": 0,
                "request_hash": "request-hash",
                "code_hash": stable_hash(source),
                "result_hash": stable_hash(metrics),
                "metrics_hash": stable_hash(metrics),
                "code_path": str(source_path),
                "result_path": str(result_path),
                "errors": [],
            }
        ],
    }
    acceptance = {
        "artifact_kind": "RuntimeArchitectTheoryExecutionPreflightAcceptance",
        "acceptance_id": "acceptance:probe",
        "source_theory_packet_id": theory["packet_id"],
        "preflight_packet_id": preflight["packet_id"],
    }
    artifacts = {
        theory["packet_id"]: theory,
        preflight["packet_id"]: preflight,
        acceptance["acceptance_id"]: acceptance,
    }

    def scratch_resolution() -> dict[str, object]:
        return build_critic_canonical_evidence_view(
            question_id="probe-resolution",
            theory_packet=theory,
            algorithm_manifest={},
            simulation_manifest={},
            formalization_manifest={},
            artifacts=artifacts,
            formal_verification_policy="optional",
        )["theory"]["independent_preflight"]["scratch_observations"][0][
            "artifact_resolution"
        ]

    view = build_critic_canonical_evidence_view(
        question_id="probe-resolution",
        theory_packet=theory,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts=artifacts,
        formal_verification_policy="optional",
    )

    resolution = view["theory"]["independent_preflight"][
        "scratch_observations"
    ][0]["artifact_resolution"]
    assert resolution["status"] == "HASH_VERIFIED"
    assert resolution["model_authored_source"] == source
    assert resolution["raw_metrics"] == metrics
    prompt = build_critic_evaluator_prompt(
        question=OpenResearchQuestion(
            id="probe-resolution",
            title="Probe resolution",
            description="Audit whether a referee probe is discriminating.",
        ),
        retrieval_manifest={},
        theory_packet=theory,
        simulation_manifest={},
        algorithm_manifest={},
        formalization_manifest={},
        canonical_evidence_view=view,
    )
    assert "easy_positive_case" in prompt

    result_path.write_text(json.dumps({"tampered": True}), encoding="utf-8")
    tampered = scratch_resolution()
    assert tampered["status"] == "HASH_MISMATCH"
    assert tampered["model_authored_source"] == ""
    assert tampered["raw_metrics"] == {}

    result_path.unlink()
    unavailable = scratch_resolution()
    assert unavailable == {"status": "UNAVAILABLE", "error_type": "FileNotFoundError"}


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


def test_canonical_evidence_view_resolves_exact_claim_revision_chain() -> None:
    def packet(packet_id: str, status: str) -> dict:
        return {
            "artifact_kind": "TheoryDerivationPacket",
            "packet_id": packet_id,
            "question": {"id": "claim-revision-chain"},
            "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
            "theory_derivation_packet": {
                "claim_index": [
                    {
                        "id": "C1",
                        "kind": "theorem",
                        "status": status,
                        "document_path": "theory.md",
                        "anchor": "C1",
                        "depends_on": [],
                    }
                ]
            },
        }

    parent = packet("theory:revision:0", "OPEN")
    middle = packet("theory:revision:1", "INCONCLUSIVE")
    current = packet("theory:revision:2", "SUPPORTED")
    first_delta = build_theory_claim_revision_delta(
        parent_theory_packet=parent,
        revised_theory_packet=middle,
    )
    second_delta = build_theory_claim_revision_delta(
        parent_theory_packet=middle,
        revised_theory_packet=current,
    )
    artifacts = {
        parent["packet_id"]: parent,
        middle["packet_id"]: middle,
        current["packet_id"]: current,
        first_delta["delta_id"]: first_delta,
        second_delta["delta_id"]: second_delta,
    }

    view = build_critic_canonical_evidence_view(
        question_id="claim-revision-chain",
        theory_packet=current,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts=artifacts,
        formal_verification_policy="optional",
    )

    history = view["theory"]["claim_revision_history"]
    assert [row["delta_id"] for row in history] == [
        first_delta["delta_id"],
        second_delta["delta_id"],
    ]
    assert history[0]["changed_claim_refs"][0]["changes"]["status"] == {
        "parent": "OPEN",
        "revised": "INCONCLUSIVE",
    }
    assert history[1]["changed_claim_refs"][0]["changes"]["status"] == {
        "parent": "INCONCLUSIVE",
        "revised": "SUPPORTED",
    }

    tampered_delta = deepcopy(second_delta)
    tampered_delta["counts"]["changed_claims"] = 99
    tampered_artifacts = {
        **artifacts,
        second_delta["delta_id"]: tampered_delta,
    }
    tampered_view = build_critic_canonical_evidence_view(
        question_id="claim-revision-chain",
        theory_packet=current,
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts=tampered_artifacts,
        formal_verification_policy="optional",
    )
    assert tampered_view["theory"]["claim_revision_history"] == []


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
        "source_replication": "optional",
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
    }


def test_source_replication_critic_loads_report_execution_and_author_reads(
    tmp_path,
) -> None:
    source_root = tmp_path / "sources"
    source_root.mkdir()
    source_text = (
        "# Public API\n"
        "The parameter documentation says the default is 10.\n"
        "def estimator(parameter=5):\n"
        "    return parameter\n"
    )
    source_path = source_root / "implementation.py"
    source_path.write_text(source_text, encoding="utf-8")
    source_manifest_path = tmp_path / "source-manifest.json"
    source_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "snapshot_id": "source-replication-snapshot",
                "source_horizon": "2026-01-01",
                "source_root": "sources",
                "documents": [
                    {
                        "document_id": "implementation",
                        "title": "Implementation",
                        "source_kind": "source_code",
                        "relative_path": "implementation.py",
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
        "implementation", line_start=1, line_end=4
    )

    report_content = (
        "# Replication report\n\n"
        "The source executed successfully. No source discrepancies were found.\n"
    )
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    report_path = workspace_dir / "report.md"
    report_path.write_text(report_content, encoding="utf-8")
    report_manifest = theory_workspace_document_manifest(
        {"report.md": report_content},
        workspace_dir=workspace_dir,
    )
    report_document = deepcopy(report_manifest["documents"][0])

    source_unsigned = {
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": "source_replication:test",
        "question_id": "source-replication-test",
        "runtime_generated": True,
        "model_authored": False,
        "command_owned_by_model": False,
        "runtime_edited_source": False,
        "artifact_identity_schema_version": 2,
        "execution_status": "EXECUTED",
        "execution_attempted": True,
        "returncode": 0,
        "source_snapshot_id": research_sources.snapshot_id,
        "source_snapshot_hash": research_sources.snapshot_hash,
        "source_commit": "public-commit",
        "executed_entrypoint_sha256": exact_source["sha256"],
        "environment_lock_sha256": "e" * 64,
        "python_version": "3.12.0",
        "package_versions": {"example": "1.0"},
        "raw_stdout": "metric=0.75\n",
        "raw_stderr": "",
        "stdout_sha256": hashlib.sha256(b"metric=0.75\n").hexdigest(),
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        "errors": [],
        "source_mutated": False,
        "staged_source_inputs_mutated": False,
        "unexpected_workspace_artifacts": [],
        "unexpected_execution_artifacts": [],
        "proof_evidence_status": (
            "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
        ),
    }
    source_manifest_hash = stable_hash(source_unsigned)
    source_manifest = {
        **source_unsigned,
        "manifest_hash": source_manifest_hash,
    }
    source_ref = {
        "artifact_id": source_manifest["artifact_id"],
        "manifest_hash": source_manifest_hash,
        "execution_status": "EXECUTED",
        "stdout_sha256": source_manifest["stdout_sha256"],
    }
    task_intent = {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "unresolved_gaps": "required",
    }
    checkpoint_body = {
        "schema_version": 1,
        "artifact_kind": "SourceReplicationCheckpoint",
        "question_id": "source-replication-test",
        "workspace_id": "source-workspace:test",
        "task_intent": task_intent,
        "source_replication_manifest_ref": source_ref,
        "report_document": report_document,
        "readiness_rationale": "Ready for independent source review.",
        "unresolved_gaps": ["Only one execution was observed."],
        "model_authored_report": True,
        "runtime_edited_report": False,
        "runtime_edited_source": False,
        "kernel_verified": False,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    checkpoint_id = (
        "source_replication_checkpoint:" + stable_hash(checkpoint_body)[:20]
    )
    checkpoint_core = {
        **checkpoint_body,
        "checkpoint_id": checkpoint_id,
    }
    workspace = {
        "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
        "artifact_id": "source_replication_workspace:test",
        "question_id": "source-replication-test",
        "disposition": "SOURCE_REPLICATION_CHECKPOINT_COMMITTED",
        "checkpoint_committed": True,
        "submitted_core_packet_hash": stable_hash(checkpoint_core),
        "model_owned_source_report": True,
        "model_owned_theory": False,
        "runtime_edited_source": False,
        "runtime_edited_theory": False,
        "kernel_verified": False,
        "changed_document_paths": ["report.md"],
        "theory_workspace_manifest": report_manifest,
        "source_replication_refs": [source_ref],
        "source_read_refs": [
            {
                "snapshot_id": research_sources.snapshot_id,
                "snapshot_hash": research_sources.snapshot_hash,
                "document_id": "implementation",
                "document_sha256": exact_source["sha256"],
                "line_start": 1,
                "line_end": 4,
                "content_sha256": exact_source["content_sha256"],
                "citation_ref": exact_source["citation_ref"],
            }
        ],
    }
    checkpoint = {
        **checkpoint_core,
        "workspace_evidence_id": workspace["artifact_id"],
        "workspace_evidence_hash": stable_hash(workspace),
        "runtime_completion_status": (
            "SOURCE_EXECUTION_RECORDED_REQUIRES_HIDDEN_EVALUATION"
        ),
        "boundary": "Source replication evidence only.",
    }
    artifacts = {
        source_manifest["artifact_id"]: source_manifest,
        workspace["artifact_id"]: workspace,
        checkpoint_id: checkpoint,
    }
    evidence_contract = {
        "source_replication_requirement": "required",
        "dimension_requirements": {
            "theory": "not_applicable",
            "scientific_code": "not_applicable",
            "empirical": "not_applicable",
            "formal": "not_applicable",
        },
    }

    view = build_critic_canonical_evidence_view(
        question_id="source-replication-test",
        theory_packet={},
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts=artifacts,
        formal_verification_policy="optional",
        evidence_contract=evidence_contract,
        research_sources=research_sources,
    )

    source_view = view["source_replication"]
    assert view["dimension_requirements"] == {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
    }
    assert source_view["lineage_verified"] is True
    assert source_view["source_execution"]["artifact_identity_schema_version"] == 2
    assert source_view["source_execution"]["unexpected_execution_artifacts"] == []
    assert source_view["report_document"]["content"] == report_content
    assert source_view["source_execution"]["raw_stdout"] == "metric=0.75\n"
    assert "source_run" not in source_view["source_execution"]
    assert "source_execution_attempts" not in source_view
    exact_observations = source_view["author_source_observations"]
    assert exact_observations["resolved_exact_source_count"] == 1
    assert exact_observations["observations"][0]["content"] == source_text.rstrip()
    assert source_view["runtime_audit"] == {
        "lineage_verified": True,
        "report_text_persisted": False,
        "source_text_persisted": False,
    }
    assert report_content not in str(source_view["runtime_audit"])

    integrated_workspace = deepcopy(workspace)
    integrated_workspace.update(
        {
            "disposition": "THEORY_CHECKPOINT_COMMITTED",
            "model_owned_theory": True,
        }
    )
    integrated_checkpoint = deepcopy(checkpoint)
    integrated_checkpoint["workspace_evidence_hash"] = stable_hash(
        integrated_workspace
    )
    integrated_view = build_critic_canonical_evidence_view(
        question_id="source-replication-test",
        theory_packet={},
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts={
            source_manifest["artifact_id"]: source_manifest,
            integrated_workspace["artifact_id"]: integrated_workspace,
            checkpoint_id: integrated_checkpoint,
        },
        formal_verification_policy="optional",
        evidence_contract=evidence_contract,
        research_sources=research_sources,
    )["source_replication"]
    assert integrated_view["lineage_verified"] is True
    assert integrated_view["report_document"]["content"] == report_content

    prompt = build_critic_evaluator_prompt(
        question=OpenResearchQuestion(
            id="source-replication-test",
            title="Source replication test",
            description="Audit one immutable source execution and report.",
        ),
        retrieval_manifest={},
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        formalization_manifest={},
        canonical_evidence_view=view,
    )
    assert "No source discrepancies were found" in prompt
    assert "The parameter documentation says the default is 10" in prompt
    assert "A zero return code establishes execution only" in prompt

    report_path.write_text("tampered", encoding="utf-8")
    tampered_view = build_critic_canonical_evidence_view(
        question_id="source-replication-test",
        theory_packet={},
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts=artifacts,
        formal_verification_policy="optional",
        evidence_contract=evidence_contract,
        research_sources=research_sources,
    )["source_replication"]
    assert tampered_view["lineage_verified"] is False
    assert tampered_view["report_document"]["content_loaded"] is False
    assert tampered_view["report_document"]["content"] == ""

    report_path.write_text(report_content, encoding="utf-8")
    source_path.write_text("tampered source\n", encoding="utf-8")
    tampered_source_view = build_critic_canonical_evidence_view(
        question_id="source-replication-test",
        theory_packet={},
        algorithm_manifest={},
        simulation_manifest={},
        formalization_manifest={},
        artifacts=artifacts,
        formal_verification_policy="optional",
        evidence_contract=evidence_contract,
        research_sources=research_sources,
    )["source_replication"]
    assert tampered_source_view["lineage_verified"] is False
    assert tampered_source_view["author_source_observations"]["observations"][0][
        "status"
    ] == "SNAPSHOT_STORAGE_IDENTITY_MISMATCH"
    assert tampered_source_view["author_source_observations"]["observations"][0][
        "content"
    ] == ""


def test_source_replication_critic_validates_model_selected_attempt_lineage(
    tmp_path,
) -> None:
    question_id = "model-selected-source-critic"
    report_content = (
        "# Reproduction report\n\nRun one completed; a later diagnostic failed.\n"
    )
    workspace_dir = tmp_path / "model-selected-workspace"
    workspace_dir.mkdir()
    (workspace_dir / "report.md").write_text(report_content, encoding="utf-8")
    report_manifest = theory_workspace_document_manifest(
        {"report.md": report_content},
        workspace_dir=workspace_dir,
    )
    report_document = deepcopy(report_manifest["documents"][0])

    manifests = []
    workspace_refs = []
    attempt_refs = []
    for source_run, execution_status in enumerate(
        ("EXECUTED", "FAILED"),
        start=1,
    ):
        raw_stdout = "estimate=0.75\n" if source_run == 1 else ""
        raw_stderr = "" if source_run == 1 else "diagnostic unavailable\n"
        unsigned_manifest = {
            "artifact_kind": "SourceReplicationManifest",
            "artifact_id": f"source_replication:model-selected:{source_run}",
            "question_id": question_id,
            "runtime_generated": True,
            "model_authored": False,
            "runtime_edited_source": False,
            "command_owned_by_model": True,
            "command_selection_mode": "model_selected",
            "command_request_hash": f"command-{source_run}",
            "execution_attempt_id": f"attempt-{source_run}",
            "execution_status": execution_status,
            "returncode": 0 if source_run == 1 else 2,
            "source_snapshot_id": "snapshot:model-selected",
            "source_snapshot_hash": "s" * 64,
            "source_commit": "commit:model-selected",
            "entrypoint_document_id": "analysis-script",
            "executed_entrypoint_sha256": "e" * 64,
            "environment_lock_sha256": "l" * 64,
            "runtime_language": "python",
            "runtime_version": "3.12.0",
            "interpreter_executable_sha256": "i" * 64,
            "interpreter_arguments": [],
            "working_directory_relative": ".",
            "arguments": [] if source_run == 1 else ["--diagnostic"],
            "runtime_environment": {},
            "package_versions": {"example": "1.0"},
            "raw_stdout": raw_stdout,
            "raw_stderr": raw_stderr,
            "stdout_sha256": hashlib.sha256(raw_stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(raw_stderr.encode()).hexdigest(),
            "errors": [] if source_run == 1 else ["research source exited 2"],
            "source_mutated": False,
            "staged_source_inputs_mutated": False,
            "unexpected_workspace_artifacts": [],
            "result_artifacts": [],
            "proof_evidence_status": (
                "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE"
            ),
        }
        manifest = {
            **unsigned_manifest,
            "manifest_hash": stable_hash(unsigned_manifest),
        }
        manifests.append(manifest)
        workspace_ref = {
            "artifact_id": manifest["artifact_id"],
            "manifest_hash": manifest["manifest_hash"],
            "execution_status": execution_status,
            "source_snapshot_hash": manifest["source_snapshot_hash"],
            "stdout_sha256": manifest["stdout_sha256"],
            "proof_evidence_status": manifest["proof_evidence_status"],
            "command_owned_by_model": True,
            "command_selection_mode": "model_selected",
            "command_request_hash": manifest["command_request_hash"],
            "execution_attempt_id": manifest["execution_attempt_id"],
        }
        workspace_refs.append(workspace_ref)
        attempt_refs.append(
            {
                "source_run": source_run,
                **{
                    key: workspace_ref[key]
                    for key in (
                        "artifact_id",
                        "manifest_hash",
                        "execution_status",
                        "command_request_hash",
                        "execution_attempt_id",
                    )
                },
            }
        )

    selected_ref = {
        key: workspace_refs[0][key]
        for key in (
            "artifact_id",
            "manifest_hash",
            "execution_status",
            "stdout_sha256",
        )
    }
    checkpoint_body = {
        "schema_version": 1,
        "artifact_kind": "SourceReplicationCheckpoint",
        "question_id": question_id,
        "workspace_id": "source-workspace:model-selected",
        "task_intent": {"source_replication": "required"},
        "source_replication_manifest_ref": selected_ref,
        "source_execution_attempt_refs": attempt_refs,
        "selected_source_run": 1,
        "report_document": report_document,
        "readiness_rationale": "The first run is the report candidate.",
        "unresolved_gaps": ["The later diagnostic did not run."],
        "model_authored_report": True,
        "runtime_edited_report": False,
        "runtime_edited_source": False,
        "kernel_verified": False,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
    }
    checkpoint_id = (
        "source_replication_checkpoint:" + stable_hash(checkpoint_body)[:20]
    )
    checkpoint_core = {**checkpoint_body, "checkpoint_id": checkpoint_id}
    workspace = {
        "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
        "artifact_id": "source_replication_workspace:model-selected",
        "question_id": question_id,
        "disposition": "SOURCE_REPLICATION_CHECKPOINT_COMMITTED",
        "checkpoint_committed": True,
        "submitted_core_packet_hash": stable_hash(checkpoint_core),
        "model_owned_source_report": True,
        "model_owned_theory": False,
        "runtime_edited_source": False,
        "runtime_edited_theory": False,
        "kernel_verified": False,
        "changed_document_paths": ["report.md"],
        "theory_workspace_manifest": report_manifest,
        "source_replication_refs": workspace_refs,
        "source_read_refs": [],
    }
    checkpoint = {
        **checkpoint_core,
        "workspace_evidence_id": workspace["artifact_id"],
        "workspace_evidence_hash": stable_hash(workspace),
        "runtime_completion_status": (
            "SOURCE_EXECUTION_RECORDED_REQUIRES_HIDDEN_EVALUATION"
        ),
    }
    artifacts = {
        **{manifest["artifact_id"]: manifest for manifest in manifests},
        workspace["artifact_id"]: workspace,
        checkpoint_id: checkpoint,
    }

    view = source_replication_evidence_view(
        question_id=question_id,
        artifacts=artifacts,
        research_sources=None,
    )

    assert view["lineage_verified"] is True
    assert view["selected_source_run"] == 1
    assert view["source_execution"]["artifact_id"] == manifests[0]["artifact_id"]
    assert [row["execution_status"] for row in view["source_execution_attempts"]] == [
        "EXECUTED",
        "FAILED",
    ]
    assert [row["selected_for_checkpoint"] for row in view["source_execution_attempts"]] == [
        True,
        False,
    ]
    assert view["runtime_audit"]["attempt_lineage_verified"] is True

    tampered_checkpoint_artifacts = deepcopy(artifacts)
    tampered_checkpoint_artifacts[checkpoint_id][
        "readiness_rationale"
    ] = "Changed after checkpoint creation."
    tampered_checkpoint_view = source_replication_evidence_view(
        question_id=question_id,
        artifacts=tampered_checkpoint_artifacts,
        research_sources=None,
    )
    assert tampered_checkpoint_view["lineage_verified"] is False
    assert "checkpoint_identity_mismatch" in tampered_checkpoint_view[
        "lineage_errors"
    ]

    tampered_artifacts = deepcopy(artifacts)
    tampered_artifacts[manifests[1]["artifact_id"]][
        "command_request_hash"
    ] = "tampered-command"
    tampered_view = source_replication_evidence_view(
        question_id=question_id,
        artifacts=tampered_artifacts,
        research_sources=None,
    )
    assert tampered_view["lineage_verified"] is False
    assert "source_execution_attempt_lineage_mismatch" in tampered_view[
        "lineage_errors"
    ]


def test_required_source_replication_blocks_unsupported_critic_acceptance() -> None:
    packet = _critic_packet()
    packet["dimension_requirements"] = {
        "source_replication": "required",
        "theory": "not_applicable",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
    }
    for row in packet["dimension_assessments"]:
        row["status"] = (
            "INCONCLUSIVE"
            if row["dimension"] == "source_replication"
            else "NOT_REQUESTED"
        )
        row["gaps"] = []
    packet["research_disposition"] = {
        "status": "ACCEPT",
        "blocking_dimensions": [],
        "rationale": "Accept the source report.",
    }

    errors = validate_critic_evaluator_packet(packet)
    assert any(error.startswith("ACCEPT evidence mismatch:") for error in errors)

    packet["dimension_assessments"][0]["status"] = "SUPPORTED"
    assert validate_critic_evaluator_packet(packet) == []


def test_required_source_replication_reports_unclean_execution() -> None:
    gaps = critic_required_dimension_evidence_gaps(
        {
            "dimension_requirements": {"source_replication": "required"},
            "source_replication": {
                "present": True,
                "lineage_verified": True,
                "report_document": {"content_loaded": True},
                "source_execution": {
                    "present": True,
                    "execution_status": "FAILED",
                    "execution_attempted": True,
                    "returncode": 0,
                    "errors": [
                        "source execution created undeclared output-root artifact"
                    ],
                    "source_mutated": False,
                    "runtime_edited_source": False,
                    "staged_source_inputs_mutated": False,
                    "unexpected_workspace_artifacts": [],
                    "unexpected_execution_artifacts": ["escaped-output.txt"],
                },
            },
        }
    )

    assert gaps == ["source_replication.execution_not_clean"]


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


def test_critic_inspects_exact_source_results_in_same_session(tmp_path) -> None:
    question_id, manifest, canonical_view, submission, csv_content = (
        _source_result_critic_fixture(tmp_path)
    )

    class SourceResultCriticBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                assert [tool.name for tool in request.tools] == [
                    CRITIC_SOURCE_RESULT_READ_TOOL,
                    CRITIC_SOURCE_RESULT_INSPECT_TOOL,
                    CRITIC_EVALUATION_SUBMIT_TOOL,
                ]
                assert str(manifest["manifest_path"]) not in (
                    request.messages[0]["content"]
                )
                calls = (
                    ClientToolCall(
                        call_id="read-exact-result",
                        name=CRITIC_SOURCE_RESULT_READ_TOOL,
                        input={
                            "artifact_id": manifest["artifact_id"],
                            "relative_path": "results.csv",
                            "line_start": 1,
                            "line_end": 2,
                        },
                    ),
                    ClientToolCall(
                        call_id="inspect-exact-figure",
                        name=CRITIC_SOURCE_RESULT_INSPECT_TOOL,
                        input={
                            "artifact_id": manifest["artifact_id"],
                            "relative_path": "figure.pdf",
                        },
                    ),
                )
            else:
                assert csv_content.splitlines()[1] in str(request.messages)
                assert "application/pdf" in str(request.messages)
                calls = (
                    ClientToolCall(
                        call_id="submit-source-result-critic",
                        name=CRITIC_EVALUATION_SUBMIT_TOOL,
                        input=deepcopy(submission),
                    ),
                )
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
                tool_calls=calls,
                text="",
                provider=self.provider_name,
                model="claude-haiku-4-5-20251001",
                metadata={"provider_stop_reason": "tool_use"},
            )

    provider = SourceResultCriticBackend()
    packet = LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
        ),
    ).propose(
        question=OpenResearchQuestion(
            id=question_id,
            title="Inspect exact reproduction results",
            description="Audit the report against its declared outputs.",
        ),
        retrieval_manifest={},
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        formalization_manifest={},
        canonical_evidence_view=canonical_view,
        source_replication_artifacts={manifest["artifact_id"]: manifest},
    )

    assert len(provider.requests) == 2
    loop = packet["client_tool_loop"]
    assert loop["transport"] == "native_same_reviewer_evidence_workspace_v4"
    assert loop["source_result_catalog_count"] == 1
    assert loop["source_result_access_count"] == 2
    assert [row["relative_path"] for row in loop["source_result_accesses"]] == [
        "results.csv",
        "figure.pdf",
    ]
    assert validate_critic_evaluator_packet(packet) == []


def test_critic_receives_changed_source_result_error_without_access_credit(
    tmp_path,
) -> None:
    question_id, manifest, canonical_view, submission, _ = (
        _source_result_critic_fixture(tmp_path)
    )
    result_path = (
        tmp_path / "source-output" / "source_workspace" / "results.csv"
    )
    result_path.write_text("method,error\ntampered,9.0\n", encoding="utf-8")
    source_assessment = next(
        row
        for row in submission["dimension_assessments"]
        if row["dimension"] == "source_replication"
    )
    source_assessment.update(
        {
            "status": "INCONCLUSIVE",
            "rationale": "The declared output no longer matches its execution hash.",
            "gaps": ["The exact source result is unavailable."],
        }
    )
    submission["gap_disclosure"]["disclosed_gaps"].append(
        "The exact source result is unavailable."
    )
    submission["research_disposition"]["blocking_dimensions"].insert(
        0, "source_replication"
    )

    class ChangedSourceResultCriticBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                calls = (
                    ClientToolCall(
                        call_id="read-changed-result",
                        name=CRITIC_SOURCE_RESULT_READ_TOOL,
                        input={
                            "artifact_id": manifest["artifact_id"],
                            "relative_path": "results.csv",
                            "line_start": 1,
                            "line_end": 2,
                        },
                    ),
                    ClientToolCall(
                        call_id="read-unbound-result",
                        name=CRITIC_SOURCE_RESULT_READ_TOOL,
                        input={
                            "artifact_id": "source_replication:not-in-checkpoint",
                            "relative_path": "results.csv",
                            "line_start": 1,
                            "line_end": 2,
                        },
                    ),
                )
            else:
                assert "source result artifact changed after execution" in str(
                    request.messages
                )
                assert "outside the verified Critic lineage" in str(
                    request.messages
                )
                calls = (
                    ClientToolCall(
                        call_id="submit-after-result-error",
                        name=CRITIC_EVALUATION_SUBMIT_TOOL,
                        input=deepcopy(submission),
                    ),
                )
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
                tool_calls=calls,
                text="",
                provider=self.provider_name,
                model="claude-haiku-4-5-20251001",
                metadata={"provider_stop_reason": "tool_use"},
            )

    provider = ChangedSourceResultCriticBackend()
    packet = LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
        ),
    ).propose(
        question=OpenResearchQuestion(
            id=question_id,
            title="Reject a changed reproduction result",
            description="Keep the reviewer on the immutable output bytes.",
        ),
        retrieval_manifest={},
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        formalization_manifest={},
        canonical_evidence_view=canonical_view,
        source_replication_artifacts={manifest["artifact_id"]: manifest},
    )

    assert len(provider.requests) == 2
    assert packet["client_tool_loop"]["source_result_access_count"] == 0
    assert validate_critic_evaluator_packet(packet) == []


def test_critic_uses_same_reviewer_document_tools_for_long_exact_evidence() -> None:
    report = (
        "The first section makes one unsupported global claim.\n"
        + "ordinary evidence line\n" * 110
        + "A later caveat does not erase the earlier claim.\n"
    )

    class ScriptedCriticBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.document_id = ""

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            turn = len(self.requests)
            if turn == 1:
                match = re.search(r'"path":"(evidence/[^"]+\.md)"', request.messages[0]["content"])
                assert match is not None
                self.document_id = match.group(1)
                calls = (
                    ClientToolCall(
                        call_id="read-report",
                        name=CRITIC_EVIDENCE_READ_TOOL,
                        input={
                            "path": self.document_id,
                            "line_start": 1,
                            "line_end": 40,
                        },
                    ),
                    ClientToolCall(
                        call_id="search-report",
                        name=CRITIC_EVIDENCE_SEARCH_TOOL,
                        input={
                            "query": "caveat",
                            "document_paths": [self.document_id],
                        },
                    ),
                )
            else:
                assert "The first section makes one unsupported global claim." in str(request.messages)
                assert "A later caveat does not erase the earlier claim." in str(request.messages)
                calls = (
                    ClientToolCall(
                        call_id="submit-critic",
                        name=CRITIC_EVALUATION_SUBMIT_TOOL,
                        input=_critic_submission(),
                    ),
                )
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
                tool_calls=calls,
                text="",
                provider=self.provider_name,
                model="claude-haiku-4-5-20251001",
                metadata={
                    "provider_stop_reason": "tool_use",
                    "provider_usage": {"input_tokens": 10, "output_tokens": 5},
                },
            )

    provider = ScriptedCriticBackend()
    agent = LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
        ),
    )
    canonical_view = {
        "artifact_kind": "CriticCanonicalEvidenceView",
        "view_hash": "canonical-view-hash",
        "dimension_requirements": {
            "source_replication": "not_applicable",
            "theory": "required",
            "scientific_code": "required",
            "empirical": "required",
            "formal": "not_applicable",
        },
        "theory": {
            "artifact_id": "theory:long-report",
            "authoritative_documents": [
                {"relative_path": "workspace.md", "content": report}
            ],
        },
    }

    packet = agent.propose(
        question=OpenResearchQuestion(
            id="critic-document-tools",
            title="Review long evidence",
            description="Inspect exact evidence through generic document tools.",
        ),
        retrieval_manifest={},
        theory_packet={"packet_id": "theory:long-report"},
        simulation_manifest={"manifest_id": "simulation:review"},
        algorithm_manifest={"manifest_id": "algorithm:review"},
        formalization_manifest={},
        canonical_evidence_view=canonical_view,
    )

    assert len(provider.requests) == 2
    first_prompt = provider.requests[0].messages[0]["content"]
    assert "ordinary evidence line" not in first_prompt
    assert "content_externalized_without_loss" in first_prompt
    assert "Only catalog path values are valid document tool paths" in first_prompt
    assert "Batch independent read/search calls" in first_prompt
    assert provider.requests[0].disable_parallel_tool_use is False
    assert provider.requests[0].metadata["strict_terminal_tool_schema"] is False
    assert provider.requests[0].metadata["reviewer_local_retry_budget"] is False
    assert packet["canonical_evidence_view_hash"] == "canonical-view-hash"
    loop = packet["client_tool_loop"]
    assert loop["transport"] == "native_same_reviewer_evidence_workspace_v4"
    assert loop["turns"] == 2
    assert loop["tool_calls"] == 3
    assert loop["document_access_count"] == 2
    assert loop["inspected_document_paths"] == [provider.document_id]
    assert loop["provider_usage"] == {"input_tokens": 20, "output_tokens": 10}
    assert loop["full_packet_regeneration_used"] is False
    assert validate_critic_evaluator_packet(packet) == []


def test_critic_omits_document_tools_when_all_evidence_is_inline() -> None:
    class DirectCriticBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            assert [tool.name for tool in request.tools] == [
                CRITIC_EVALUATION_SUBMIT_TOOL
            ]
            assert request.tool_choice == CRITIC_EVALUATION_SUBMIT_TOOL
            call = ClientToolCall(
                call_id="submit-inline-critic",
                name=CRITIC_EVALUATION_SUBMIT_TOOL,
                input=_critic_submission(),
            )
            return ClientToolTurnResponse(
                content_blocks=(
                    {
                        "type": "tool_use",
                        "id": call.call_id,
                        "name": call.name,
                        "input": dict(call.input),
                    },
                ),
                tool_calls=(call,),
                text="",
                provider=self.provider_name,
                model="claude-haiku-4-5-20251001",
                metadata={"provider_stop_reason": "tool_use"},
            )

    provider = DirectCriticBackend()
    packet = LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
        ),
    ).propose(
        question=OpenResearchQuestion(
            id="critic-inline-evidence",
            title="Review inline evidence",
            description="Submit directly when no external evidence document exists.",
        ),
        retrieval_manifest={},
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={"manifest_id": "algorithm:inline"},
        formalization_manifest={},
        canonical_evidence_view={
            "artifact_kind": "CriticCanonicalEvidenceView",
            "view_hash": "critic-inline-view",
            "dimension_requirements": {
                "source_replication": "not_applicable",
                "theory": "required",
                "scientific_code": "required",
                "empirical": "required",
                "formal": "not_applicable",
            },
        },
    )

    assert len(provider.requests) == 1
    assert "no external evidence document tools are available" in (
        provider.requests[0].messages[0]["content"]
    )
    assert packet["client_tool_loop"]["turns"] == 1
    assert packet["client_tool_loop"]["tool_calls"] == 1
    assert packet["client_tool_loop"]["document_access_count"] == 0
    assert validate_critic_evaluator_packet(packet) == []


def test_critic_terminal_submission_waits_for_same_turn_read_observation() -> None:
    report = "load-bearing source line\n" * 100

    class ReadThenSubmitCriticBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []
            self.document_id = ""

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            if len(self.requests) == 1:
                match = re.search(
                    r'"path":"(evidence/[^"]+\.md)"',
                    request.messages[0]["content"],
                )
                assert match is not None
                self.document_id = match.group(1)
                calls = (
                    ClientToolCall(
                        call_id="read-before-submit",
                        name=CRITIC_EVIDENCE_READ_TOOL,
                        input={
                            "path": self.document_id,
                            "line_start": 1,
                            "line_end": 10,
                        },
                    ),
                    ClientToolCall(
                        call_id="premature-submit",
                        name=CRITIC_EVALUATION_SUBMIT_TOOL,
                        input=_critic_submission(),
                    ),
                )
            else:
                assert "critic terminal submission must be the only call" in str(
                    request.messages
                )
                calls = (
                    ClientToolCall(
                        call_id="informed-submit",
                        name=CRITIC_EVALUATION_SUBMIT_TOOL,
                        input=_critic_submission(),
                    ),
                )
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
                tool_calls=calls,
                text="",
                provider=self.provider_name,
                model="claude-haiku-4-5-20251001",
                metadata={"provider_stop_reason": "tool_use"},
            )

    provider = ReadThenSubmitCriticBackend()
    packet = LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
        ),
    ).propose(
        question=OpenResearchQuestion(
            id="critic-causal-terminal",
            title="Review exact evidence before judgment",
            description="Make the terminal judgment after receiving evidence.",
        ),
        retrieval_manifest={},
        theory_packet={"packet_id": "theory:causal-terminal"},
        simulation_manifest={},
        algorithm_manifest={},
        formalization_manifest={},
        canonical_evidence_view={
            "artifact_kind": "CriticCanonicalEvidenceView",
            "view_hash": "critic-causal-terminal-view",
            "dimension_requirements": {
                "source_replication": "not_applicable",
                "theory": "required",
                "scientific_code": "required",
                "empirical": "required",
                "formal": "not_applicable",
            },
            "theory": {
                "artifact_id": "theory:causal-terminal",
                "authoritative_documents": [
                    {"relative_path": "workspace.md", "content": report}
                ],
            },
        },
    )

    assert len(provider.requests) == 2
    assert packet["client_tool_loop"]["turns"] == 2
    assert packet["client_tool_loop"]["tool_calls"] == 3
    assert packet["client_tool_loop"]["document_access_count"] == 1
    assert validate_critic_evaluator_packet(packet) == []


@pytest.mark.parametrize(
    "schema_defect",
    [None, "missing_nested_field", "wrong_nested_type", "extra_field", "missing_dimension"],
)
def test_critic_corrects_invalid_judgment_in_same_retained_session(
    schema_defect: str | None,
) -> None:
    invalid = _critic_submission()
    for row in invalid["dimension_assessments"]:
        if row["dimension"] == "theory":
            row["status"] = "INCONCLUSIVE"
            row["gaps"] = ["Theory evidence is incomplete."]
        elif row["dimension"] in {"scientific_code", "empirical"}:
            row["status"] = "SUPPORTED"
            row["gaps"] = []
    invalid["research_disposition"] = {
        "status": "ACCEPT",
        "blocking_dimensions": [],
        "rationale": "The first judgment incorrectly accepts incomplete theory.",
    }
    corrected = deepcopy(invalid)
    corrected["research_disposition"] = {
        "status": "INCONCLUSIVE",
        "blocking_dimensions": ["theory"],
        "rationale": "Required theory evidence remains incomplete.",
    }
    if schema_defect:
        invalid = deepcopy(corrected)
        if schema_defect == "missing_nested_field":
            del invalid["gap_disclosure"]["rationale"]
        elif schema_defect == "wrong_nested_type":
            invalid["evidence_boundary_audit"][0]["boundary_ok"] = "true"
        elif schema_defect == "extra_field":
            invalid["research_disposition"]["runtime_override"] = "ACCEPT"
        elif schema_defect == "missing_dimension":
            invalid["dimension_assessments"].pop()

    class CorrectingCriticBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.requests = []

        def generate_client_tool_turn(self, request):
            self.requests.append(request)
            payload = invalid if len(self.requests) == 1 else corrected
            call = ClientToolCall(
                call_id=f"submit-critic-{len(self.requests)}",
                name=CRITIC_EVALUATION_SUBMIT_TOOL,
                input=deepcopy(payload),
            )
            return ClientToolTurnResponse(
                content_blocks=(
                    {
                        "type": "tool_use",
                        "id": call.call_id,
                        "name": call.name,
                        "input": dict(call.input),
                    },
                ),
                tool_calls=(call,),
                text="",
                provider=self.provider_name,
                model="claude-haiku-4-5-20251001",
                metadata={"provider_stop_reason": "tool_use"},
            )

    provider = CorrectingCriticBackend()
    packet = LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
        ),
    ).propose(
        question=OpenResearchQuestion(
            id="critic-same-session-correction",
            title="Correct one invalid Critic judgment",
            description="Use the validator observation in the retained session.",
        ),
        retrieval_manifest={},
        theory_packet={},
        simulation_manifest={},
        algorithm_manifest={},
        formalization_manifest={},
        canonical_evidence_view={
            "artifact_kind": "CriticCanonicalEvidenceView",
            "view_hash": "critic-correction-view",
            "dimension_requirements": {
                "source_replication": "not_applicable",
                "theory": "required",
                "scientific_code": "required",
                "empirical": "required",
                "formal": "not_applicable",
            },
        },
    )

    assert len(provider.requests) == 2
    assert provider.requests[0].tools[-1].strict is False
    assert provider.requests[0].tools[-1].input_schema == CRITIC_EVALUATOR_JSON_SCHEMA
    expected_feedback = (
        "critic submission schema rejected:"
        if schema_defect
        else "ACCEPT evidence mismatch:"
    )
    assert expected_feedback in str(provider.requests[1].messages)
    assert packet["research_disposition"]["status"] == "INCONCLUSIVE"
    assert packet["client_tool_loop"]["turns"] == 2
    assert validate_critic_evaluator_packet(packet) == []


def test_failed_critic_session_preserves_last_submission_and_exact_errors() -> None:
    invalid = _critic_submission()
    for row in invalid["dimension_assessments"]:
        if row["dimension"] == "theory":
            row["status"] = "INCONCLUSIVE"
            row["gaps"] = ["Theory evidence is incomplete."]
        elif row["dimension"] in {"scientific_code", "empirical"}:
            row["status"] = "SUPPORTED"
            row["gaps"] = []
    invalid["research_disposition"] = {
        "status": "ACCEPT",
        "blocking_dimensions": [],
        "rationale": "The model incorrectly accepts an incomplete required dimension.",
    }

    class RepeatingInvalidCriticBackend:
        provider_name = "anthropic"

        def __init__(self) -> None:
            self.calls = 0

        def generate_client_tool_turn(self, request):
            self.calls += 1
            call = ClientToolCall(
                call_id=f"submit-invalid-{self.calls}",
                name=CRITIC_EVALUATION_SUBMIT_TOOL,
                input=deepcopy(invalid),
            )
            return ClientToolTurnResponse(
                content_blocks=(
                    {
                        "type": "tool_use",
                        "id": call.call_id,
                        "name": call.name,
                        "input": dict(call.input),
                    },
                ),
                tool_calls=(call,),
                text="",
                provider=self.provider_name,
                model="claude-haiku-4-5-20251001",
                metadata={"provider_stop_reason": "tool_use"},
            )

    provider = RepeatingInvalidCriticBackend()
    agent = LLMCriticEvaluatorAgent(
        provider=provider,
        config=CriticEvaluatorConfig(
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            provider_name="anthropic",
            client_tool_max_no_progress_turns=1,
        ),
    )
    canonical_view = {
        "artifact_kind": "CriticCanonicalEvidenceView",
        "view_hash": "critic-failure-view",
        "dimension_requirements": {
            "source_replication": "not_applicable",
            "theory": "required",
            "scientific_code": "required",
            "empirical": "required",
            "formal": "not_applicable",
        },
    }

    try:
        agent.propose(
            question=OpenResearchQuestion(
                id="critic-failed-terminal-session",
                title="Preserve a rejected critic terminal packet",
                description="Return exact validator observations to one reviewer session.",
            ),
            retrieval_manifest={},
            theory_packet={},
            simulation_manifest={},
            algorithm_manifest={},
            formalization_manifest={},
            canonical_evidence_view=canonical_view,
        )
    except PacketValidationError as exc:
        assert provider.calls == 2
        assert exc.attempts == 2
        assert exc.last_invalid_packet is not None
        assert exc.last_invalid_packet["research_disposition"]["status"] == "ACCEPT"
        feedback_history = json.dumps(exc.history, sort_keys=True)
        assert "ACCEPT evidence mismatch:" in feedback_history
        assert "theory" in feedback_history and "INCONCLUSIVE" in feedback_history
    else:
        raise AssertionError("invalid repeated Critic submissions must fail closed")

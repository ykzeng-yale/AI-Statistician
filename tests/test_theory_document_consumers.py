from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.algorithm_engineer_llm import (
    _algorithm_engineer_response_schema,
    _compact_theory_packet_for_algorithm,
    materialize_algorithm_source_workspace_packet,
)
from ai_statistician.architect_theory_execution_preflight import (
    build_architect_theory_execution_preflight_material,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.formalizer_llm import (
    _build_lean_candidate_workspace_tool_prompt,
    _formalizer_json_schema,
    build_formalizer_prompt,
)
from ai_statistician.generated_code_semantic_review_scope import (
    generated_code_semantic_review_theory_projection,
)
from ai_statistician.metric_protocol_stage import (
    build_theory_informed_metric_protocol_material,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.simulation_engineer_llm import (
    _compact_theory_packet_for_simulation,
    _simulation_engineer_response_schema,
)
from ai_statistician.theory_derivation_trace import (
    document_authoritative_theory_context,
    theory_trace_alignment_contract,
    theory_trace_consumption_contract,
)
from ai_statistician.theory_revision_lineage import (
    build_theory_claim_revision_delta,
)
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    THEORY_WORKSPACE_HANDOFF_ROLE,
    theory_workspace_document_manifest,
)


def _document_theory_packet(tmp_path: Path) -> tuple[dict, str]:
    content = (
        "# C0\n\nAssume the admitted law is integrable.\n\n"
        "# C1\n\nFor every admitted law, $E[Z] = 0$.\n"
    )
    documents = {"derivations/C1.md": content}
    target = tmp_path / "derivations" / "C1.md"
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")
    return (
        {
            "artifact_kind": "TheoryDerivationPacket",
            "packet_id": "theory:C1",
            "question": {"id": "question:C1"},
            "problem_card": {
                "estimand": "E[Z]",
                "assumptions": ["integrability"],
                "desired_theorem_type": "identity",
            },
            "theory_derivation_packet": {
                "derivation_summary": "The exact derivation is in C1.md.",
                "claim_index": [
                    {
                        "id": "C0",
                        "kind": "assumption",
                        "document_path": "derivations/C1.md",
                        "anchor": "C0",
                        "depends_on": [],
                        "status": "SUPPORTED",
                    },
                    {
                        "id": "C1",
                        "kind": "theorem",
                        "document_path": "derivations/C1.md",
                        "anchor": "C1",
                        "depends_on": ["C0"],
                        "status": "SUPPORTED",
                    }
                ],
                "sanity_check_index": [
                    {
                        "id": "check-C1",
                        "claim_ref": "C1",
                        "document_path": "derivations/C1.md",
                        "anchor": "C1",
                        "status": "PASS",
                    }
                ],
            },
            "estimator_specs": [],
            "theorem_cards": [{"id": "C1", "conclusion": "E[Z] = 0"}],
            "lemma_cards": [],
            "simulation_ademp_spec": {},
            "theory_workspace_manifest": theory_workspace_document_manifest(
                documents,
                workspace_dir=tmp_path,
            ),
            "theory_content_authority": THEORY_WORKSPACE_CONTENT_AUTHORITY,
            "structured_handoff_role": THEORY_WORKSPACE_HANDOFF_ROLE,
        },
        content,
    )


def test_every_theory_consumer_reads_the_same_hash_bound_document(
    tmp_path: Path,
) -> None:
    packet, content = _document_theory_packet(tmp_path)

    algorithm = _compact_theory_packet_for_algorithm(packet)
    simulation = _compact_theory_packet_for_simulation(packet)
    review = generated_code_semantic_review_theory_projection(
        theory_packet=packet,
        proposal_packet={},
    )
    expected_rows = algorithm["authoritative_theory_documents"]

    assert expected_rows == simulation["authoritative_theory_documents"]
    assert expected_rows == review["authoritative_theory_documents"]
    assert expected_rows[0]["path"] == "derivations/C1.md"
    assert expected_rows[0]["content"] == content
    assert len(expected_rows[0]["sha256"]) == 64

    formalizer_prompt = build_formalizer_prompt(
        question=OpenResearchQuestion(
            id="question:C1",
            title="Check C1",
            description="Formalize one file-backed theory claim.",
        ),
        theory_packet=packet,
        simulation_manifest={},
        algorithm_manifest={},
        registered_problem={},
        theorem_goals=[
            {
                "id": "C1",
                "informal_statement": "For every admitted law, E[Z] = 0.",
            }
        ],
    )
    formalizer_payload = json.loads(
        formalizer_prompt[formalizer_prompt.index("{") :]
    )
    assert formalizer_payload["theory_packet_summary"][
        "authoritative_theory_documents"
    ] == expected_rows
    formalizer_claim = next(
        row
        for row in formalizer_payload["theory_packet_summary"][
            "theory_derivation_trace"
        ]["claim_index"]
        if row["id"] == "C1"
    )
    assert formalizer_claim["depends_on"] == ["C0"]
    revision_payload = json.loads(
        _build_lean_candidate_workspace_tool_prompt(
            question=OpenResearchQuestion(
                id="question:C1",
                title="Check C1",
                description="Revise one file-backed Lean candidate.",
            ),
            theory_packet=packet,
            parent_packet={
                "packet_id": "formalizer:C1",
                "formal_targets": [
                    {
                        "id": "C1",
                        "informal_source": (
                            "For every admitted law, E[Z] = 0."
                        ),
                    }
                ],
            },
            candidate_id="C1",
            candidate_source_field="lean_source",
            candidate_lean_declaration="C1",
            initial_source="theorem C1 : True := by trivial\n",
            environment_feedback={},
        )
    )
    assert revision_payload["task_bound_theory_context"][
        "authoritative_theory_documents"
    ] == expected_rows

    parent_packet = json.loads(json.dumps(packet))
    parent_packet["packet_id"] = "theory:C1:parent"
    parent_claim = next(
        row
        for row in parent_packet["theory_derivation_packet"]["claim_index"]
        if row["id"] == "C1"
    )
    parent_claim["status"] = "OPEN"
    claim_revision_delta = build_theory_claim_revision_delta(
        parent_theory_packet=parent_packet,
        revised_theory_packet=packet,
    )
    semantic = build_theory_informed_metric_protocol_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
        theory_claim_revision_delta=claim_revision_delta,
    )
    preflight = build_architect_theory_execution_preflight_material(
        question=OpenResearchQuestion(
            id="question:C1",
            title="Check C1",
            description="Review one file-backed theory claim.",
        ),
        theory_protocol_material=semantic,
        upstream_research_contract={"formal_targets": [], "simulation_targets": []},
    )
    document_anchor = next(
        row
        for row in preflight["anchor_catalog"]
        if row["artifact_role"] == "authoritative_theory_document"
    )
    claim_graph_anchor = next(
        row
        for row in preflight["anchor_catalog"]
        if row["artifact_role"] == "document_claim_dependency_index"
    )
    revision_delta_anchor = next(
        row
        for row in preflight["anchor_catalog"]
        if row["artifact_role"] == "claim_revision_delta"
    )
    assert document_anchor["content"] == content
    assert document_anchor["content_sha256"] == expected_rows[0]["sha256"]
    claim_row = next(
        row for row in claim_graph_anchor["content"] if row["id"] == "C1"
    )
    compact_claim_row = next(
        row
        for row in algorithm["theory_derivation_trace"]["claim_index"]
        if row["id"] == "C1"
    )
    simulation_claim_row = next(
        row
        for row in simulation["theory_derivation_trace"]["claim_index"]
        if row["id"] == "C1"
    )
    consumption = theory_trace_consumption_contract(
        packet,
        consumer_subsystem="AlgorithmEngineer",
    )
    assert claim_row["depends_on"] == ["C0"]
    assert compact_claim_row["depends_on"] == ["C0"]
    assert simulation_claim_row["depends_on"] == ["C0"]
    assert consumption["n_claim_dependency_edges_supplied"] == 1
    assert revision_delta_anchor["content"]["changed_claim_refs"][0][
        "claim_id"
    ] == "C1"


def test_document_authority_replaces_duplicate_structured_math_for_coding_agents(
    tmp_path: Path,
) -> None:
    packet, content = _document_theory_packet(tmp_path)
    packet["problem_card"] = {
        "estimand": "DUPLICATE_PROBLEM_PROSE",
        "assumptions": ["DUPLICATE_ASSUMPTION_PROSE"],
        "desired_theorem_type": "DUPLICATE_THEOREM_TYPE",
    }
    packet["estimator_specs"] = [
        {
            "id": "C1",
            "name": "document-owned estimator",
            "formula": "DUPLICATE_FORMULA_PROSE",
            "algorithm_sketch": "DUPLICATE_ALGORITHM_PROSE",
            "estimator_interface_contract": {
                "request_fields": [
                    {
                        "name": "observations",
                        "meaning": "Finite numeric array.",
                        "binding": "per_replicate_data",
                    }
                ],
                "response_fields": [
                    {
                        "name": "estimate",
                        "meaning": "Finite estimate.",
                        "normalization": "Defined in C1.",
                        "derivation_ref": "C1",
                    }
                ],
            },
            "estimator_interface_contract_id": "abi:C1",
        }
    ]
    packet["theorem_cards"] = [
        {"id": "C1", "conclusion": "DUPLICATE_THEOREM_PROSE"}
    ]
    packet["simulation_ademp_spec"] = {
        "aim": "DUPLICATE_SIMULATION_PROSE",
        "dgps": ["DUPLICATE_DGP_PROSE"],
    }

    context = document_authoritative_theory_context(packet)
    algorithm = _compact_theory_packet_for_algorithm(packet)
    simulation = _compact_theory_packet_for_simulation(packet)

    assert context["document_authoritative"] is True
    assert context["authoritative_theory_documents"][0]["content"] == content
    assert algorithm["authoritative_theory_documents"] == context[
        "authoritative_theory_documents"
    ]
    assert simulation["authoritative_theory_documents"] == context[
        "authoritative_theory_documents"
    ]
    assert "problem_card" not in algorithm
    assert "theorem_cards" not in algorithm
    assert "simulation_ademp_spec" not in algorithm
    assert "problem_card" not in simulation
    assert "theorem_cards" not in simulation
    assert "simulation_ademp_spec" not in simulation
    assert set(algorithm["estimator_specs"][0]) == {
        "id",
        "name",
        "estimator_interface_contract",
        "estimator_interface_contract_id",
    }
    assert set(simulation["estimator_specs"][0]) == {"id", "name"}
    assert algorithm["estimator_specs"][0]["estimator_interface_contract"][
        "response_fields"
    ][0]["derivation_ref"] == "C1"
    serialized = json.dumps(
        {"algorithm": algorithm, "simulation": simulation},
        sort_keys=True,
    )
    for duplicate in (
        "DUPLICATE_PROBLEM_PROSE",
        "DUPLICATE_ASSUMPTION_PROSE",
        "DUPLICATE_THEOREM_TYPE",
        "DUPLICATE_FORMULA_PROSE",
        "DUPLICATE_ALGORITHM_PROSE",
        "DUPLICATE_THEOREM_PROSE",
        "DUPLICATE_SIMULATION_PROSE",
        "DUPLICATE_DGP_PROSE",
    ):
        assert duplicate not in serialized


def test_source_workspace_review_packet_does_not_duplicate_theory_math(
    tmp_path: Path,
) -> None:
    packet, content = _document_theory_packet(tmp_path)
    packet["estimator_specs"] = [
        {
            "id": "C1",
            "name": "document-owned estimator",
            "estimator_interface_contract": {
                "request_fields": [
                    {
                        "name": "observations",
                        "meaning": "Finite numeric array.",
                        "binding": "per_replicate_data",
                    }
                ],
                "response_fields": [
                    {
                        "name": "estimate",
                        "meaning": "Finite estimate.",
                        "normalization": "Defined in C1.",
                        "derivation_ref": "C1",
                    }
                ],
            },
        }
    ]
    source = "def run_estimator(request): return {'estimate': 0.0}\n"
    source_hash = stable_hash(source)
    review_packet = materialize_algorithm_source_workspace_packet(
        question=OpenResearchQuestion(
            id="question:C1",
            title="Implement C1",
            description="Implement the document-owned estimator.",
        ),
        theory_packet=packet,
        implementation_gaps=[{"estimator_id": "C1"}],
        source_rows=[
            {
                "estimator_id": "C1",
                "source_code": source,
                "script_hash": source_hash,
                "smoke_passed": True,
                "scientific_code_workspace": {
                    "artifact_id": "question:C1:C1",
                    "provider": "anthropic",
                    "model": "claude-haiku-4-5-20251001",
                    "model_tier": "haiku",
                    "accepted": True,
                    "model_owned_source": True,
                    "runtime_edited_source": False,
                    "transcript_fingerprint": "transcript:C1",
                },
            }
        ],
    )

    assert review_packet["source_workspace_planning_owned"] is True
    assert review_packet["planning_model_call_used"] is False
    assert review_packet["source_workspace_artifacts"] == [
        {
            "estimator_id": "C1",
            "source_hash": source_hash,
            "workspace_artifact_id": "question:C1:C1",
            "workspace_transcript_fingerprint": "transcript:C1",
        }
    ]
    assert review_packet["theory_trace_alignment_contract"][
        "structured_alignment_observed"
    ] is False
    review = generated_code_semantic_review_theory_projection(
        theory_packet=packet,
        proposal_packet=review_packet,
    )
    assert review["theory_review_projection"]["projection_mode"] == (
        "canonical_semantic_core_fallback"
    )
    assert review["authoritative_theory_documents"][0]["content"] == content


def test_document_claim_dag_is_complete_and_exact_across_subagents(
    tmp_path: Path,
) -> None:
    packet, _ = _document_theory_packet(tmp_path)
    content = "\n".join(
        f"# C{index}\n\nClaim C{index}.\n" for index in range(6)
    )
    document_path = "derivations/C1.md"
    (tmp_path / document_path).write_text(content, encoding="utf-8")
    packet["theory_workspace_manifest"] = theory_workspace_document_manifest(
        {document_path: content},
        workspace_dir=tmp_path,
    )
    packet["theory_derivation_packet"]["derivation_steps"] = [
        {
            "id": f"D{index}",
            "claim": f"legacy claim {index}",
            "depends_on": [],
        }
        for index in range(6)
    ]
    packet["theory_derivation_packet"]["claim_index"] = [
        {
            "id": "C0",
            "kind": "assumption",
            "document_path": document_path,
            "anchor": "C0",
            "depends_on": [],
            "status": "SUPPORTED",
        },
        {
            "id": "C1",
            "kind": "lemma",
            "document_path": document_path,
            "anchor": "C1",
            "depends_on": ["C0"],
            "status": "SUPPORTED",
        },
        {
            "id": "C2",
            "kind": "theorem",
            "document_path": document_path,
            "anchor": "C2",
            "depends_on": ["C1"],
            "status": "SUPPORTED",
        },
        {
            "id": "C3",
            "kind": "assumption",
            "document_path": document_path,
            "anchor": "C3",
            "depends_on": [],
            "status": "SUPPORTED",
        },
        {
            "id": "C4",
            "kind": "lemma",
            "document_path": document_path,
            "anchor": "C4",
            "depends_on": ["C3"],
            "status": "SUPPORTED",
        },
        {
            "id": "C5",
            "kind": "theorem",
            "document_path": document_path,
            "anchor": "C5",
            "depends_on": ["C4"],
            "status": "SUPPORTED",
        },
    ]

    algorithm = _compact_theory_packet_for_algorithm(packet)
    simulation = _compact_theory_packet_for_simulation(packet)
    assert len(algorithm["theory_derivation_trace"]["derivation_steps"]) == 3
    assert [
        row["id"] for row in algorithm["theory_derivation_trace"]["claim_index"]
    ] == ["C0", "C1", "C2", "C3", "C4", "C5"]
    assert simulation["theory_derivation_trace"]["claim_index"] == algorithm[
        "theory_derivation_trace"
    ]["claim_index"]

    consumption = theory_trace_consumption_contract(
        packet,
        consumer_subsystem="AlgorithmEngineer",
        max_rows=3,
    )
    assert consumption["n_claim_index_rows_supplied"] == 6
    assert consumption["n_claim_dependency_edges_supplied"] == 4

    alignment = theory_trace_alignment_contract(
        packet,
        {
            "referenced_claim_ids": ["C2"],
            "rationale": "The generated estimator directly realizes C2.",
        },
        consumer_subsystem="AlgorithmEngineer",
        max_rows=3,
    )
    assert alignment["alignment_mode"] == "exact_claim_id_v1"
    assert alignment["structured_alignment_observed"] is True
    assert alignment["supported_claim_ids"] == ["C2"]
    assert alignment["claim_dependency_closure"] == ["C0", "C1", "C2"]

    fuzzy_alias = theory_trace_alignment_contract(
        packet,
        {
            "referenced_claim_ids": ["c2"],
            "rationale": "Case-changing an identity must not bind it.",
        },
        consumer_subsystem="AlgorithmEngineer",
        max_rows=3,
    )
    assert fuzzy_alias["structured_alignment_observed"] is False
    assert fuzzy_alias["unsupported_claim_ids"] == ["c2"]

    algorithm_schema = _algorithm_engineer_response_schema(
        implementation_gaps=[{"estimator_id": "candidate-a"}],
        requires_generated_code=True,
        theory_packet=packet,
    )
    simulation_schema = _simulation_engineer_response_schema(
        authoritative_metric_requirements=[],
        requires_generated_code=True,
        requires_typed_metric_contracts=False,
        theory_packet=packet,
    )
    formalizer_schema = _formalizer_json_schema(theory_packet=packet)
    for schema in (algorithm_schema, simulation_schema, formalizer_schema):
        alignment_schema = schema["properties"]["theory_trace_alignment"]
        assert set(alignment_schema["properties"]) == {
            "referenced_claim_ids",
            "rationale",
        }
        assert alignment_schema["properties"]["referenced_claim_ids"]["items"][
            "enum"
        ] == ["C0", "C1", "C2", "C3", "C4", "C5"]

    review = generated_code_semantic_review_theory_projection(
        theory_packet=packet,
        proposal_packet={
            "theory_trace_alignment_contract": alignment,
            "implementation_targets": [],
        },
    )
    assert [
        row["id"]
        for row in review["theory_derivation_packet"]["claim_index"]
    ] == ["C0", "C1", "C2"]
    projection = review["theory_review_projection"]
    assert projection["supported_claim_ids"] == ["C2"]
    assert projection["claim_dependency_closure"] == ["C0", "C1", "C2"]

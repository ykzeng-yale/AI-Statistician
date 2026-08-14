from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.algorithm_engineer_llm import (
    _compact_theory_packet_for_algorithm,
)
from ai_statistician.architect_theory_execution_preflight import (
    build_architect_theory_execution_preflight_material,
)
from ai_statistician.generated_code_semantic_review_scope import (
    generated_code_semantic_review_theory_projection,
)
from ai_statistician.formalizer_llm import (
    _build_lean_candidate_workspace_tool_prompt,
    build_formalizer_prompt,
)
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.simulation_engineer_llm import (
    _compact_theory_packet_for_simulation,
)
from ai_statistician.theory_derivation_trace import (
    theory_trace_consumption_contract,
)
from ai_statistician.theory_semantic_material import build_theory_semantic_material
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

    semantic = build_theory_semantic_material(
        theory_packet=packet,
        theory_packet_id=packet["packet_id"],
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

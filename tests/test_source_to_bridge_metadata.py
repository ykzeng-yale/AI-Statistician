from __future__ import annotations

from ai_statistician import source_to_bridge_metadata as metadata


def test_metadata_request_row_normalizes_scalar_list_fields() -> None:
    row = metadata.metadata_authoring_request_row(
        request={
            "candidate_request_id": "request:hGoodCovered",
            "premise_name": "hGoodCovered",
            "target_theorem_name": "split_conformal_finite_sample_coverage",
            "target_lean_declaration": "split_conformal_finite_sample_coverage",
            "exact_source_theorem_binders": {"name": "hexch", "type": "Exchangeable"},
            "premise_semantic_anchor_binder_names": "hC",
            "required_semantic_anchor_reference_names": "hC",
            "adapter_object_names_requiring_source_instantiation": "covered",
        },
        proposal_packet={"packet_id": "formalizer_proposal:test"},
        proof_bank_runtime_memory_summary={},
        theorem_goal_ids=["split_conformal_finite_sample_coverage"],
        source_kind="explicit_formalizer_candidate_request",
        source_index=1,
        schema_version=1,
        proof_evidence_boundary="kernel boundary",
    )

    assert row["request_complete"] is True
    assert row["exact_source_theorem_binders"] == [
        {"name": "hexch", "type": "Exchangeable"}
    ]
    assert row["premise_semantic_anchor_binder_names"] == ["hC"]
    assert row["required_semantic_anchor_reference_names"] == ["hC"]
    assert row["adapter_object_names_requiring_source_instantiation"] == ["covered"]


def test_memory_rows_normalize_compacted_scalar_request_fields() -> None:
    rows = metadata.memory_metadata_authoring_request_rows(
        [
            {
                "artifact_kind": metadata.ARTIFACT_KIND,
                "learning_task": metadata.LEARNING_TASK,
                "candidate_request_id": "request:hGoodCovered",
                "premise_name": "hGoodCovered",
                "target_theorem_name": "split_conformal_finite_sample_coverage",
                "target_lean_declaration": "split_conformal_finite_sample_coverage",
                "exact_source_theorem_binders": [
                    {"name": "hexch", "type": "Exchangeable"}
                ],
                "premise_semantic_anchor_binder_names": "hC",
                "required_semantic_anchor_reference_names": "hC",
                "adapter_object_names_requiring_source_instantiation": "covered",
            }
        ],
        row_trigger=lambda row, input_summary: row.get("trigger", ""),
    )

    assert len(rows) == 1
    assert rows[0]["request_complete"] is True
    assert rows[0]["premise_semantic_anchor_binder_names"] == ["hC"]
    assert rows[0]["required_semantic_anchor_reference_names"] == ["hC"]
    assert rows[0]["adapter_object_names_requiring_source_instantiation"] == [
        "covered"
    ]

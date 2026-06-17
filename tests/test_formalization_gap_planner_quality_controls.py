from ai_statistician.formalization_gap_planner_quality_controls import (
    QUALITY_CONTROL_FIELDS,
    normalize_target_prover_family,
    project_quality_control_payload_to_target,
    quality_control_payload_from_mapping,
    quality_control_projection_trace,
    resource_contract_target_prover_family,
)


def test_quality_control_projection_targets_prover_feedback_contracts() -> None:
    payload = {
        "resource_contract_ids": ["lean_lsp:proof_state_feedback"],
        "required_quality_signals": ["diagnostic_signature"],
        "response_validation_signals": ["residual_goals_or_diagnostics_present"],
    }

    projected = project_quality_control_payload_to_target(
        payload,
        target_prover_family="coq",
    )

    assert projected["resource_contract_ids"] == (
        "rocq_lsp_serapi:proof_state_feedback",
    )
    assert projected["required_quality_signals"] == ("diagnostic_signature",)
    assert projected["response_validation_signals"] == (
        "residual_goals_or_diagnostics_present",
    )
    assert quality_control_payload_from_mapping(payload)["resource_contract_ids"] == (
        "lean_lsp:proof_state_feedback",
    )
    trace = quality_control_projection_trace(
        source_controls=quality_control_payload_from_mapping(payload),
        projected_controls=projected,
        target_prover_family="coq",
    )
    assert trace["target_prover_family"] == "rocq"
    assert trace["source_resource_contract_ids"] == [
        "lean_lsp:proof_state_feedback",
    ]
    assert trace["projected_resource_contract_ids"] == [
        "rocq_lsp_serapi:proof_state_feedback",
    ]
    assert trace["changed_resource_contract_ids"] is True


def test_quality_control_projection_preserves_unknown_nonproof_contracts() -> None:
    payload = {"resource_contract_ids": ["paperclip:source_snippet_contract"]}

    projected = project_quality_control_payload_to_target(
        payload,
        target_prover_family="rocq",
    )

    assert projected["resource_contract_ids"] == (
        "paperclip:source_snippet_contract",
    )
    assert resource_contract_target_prover_family(
        "lean_lsp:proof_state_feedback"
    ) == "lean4"
    assert normalize_target_prover_family("isabelle/hol") == "isabelle"
    assert "resource_contract_ids" in QUALITY_CONTROL_FIELDS

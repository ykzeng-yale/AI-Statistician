from __future__ import annotations

from ai_statistician.generated_metric_repair_policy import (
    generated_metric_gate_repair_instruction,
)


def test_metric_gate_repair_instruction_preserves_typed_authority() -> None:
    prompt = generated_metric_gate_repair_instruction(
        artifact_label="generated algorithm draft"
    )

    assert "contract_id, requirement_id, artifact_id, metric_path" in prompt
    assert "operator, threshold/lower/upper, tolerance" in prompt
    assert "authority lineage unchanged" in prompt
    assert "invent a new required gate" in prompt
    assert "empirical execution evidence only" in prompt


def test_metric_gate_repair_instruction_contains_no_statistical_family_rule() -> None:
    prompt = generated_metric_gate_repair_instruction(
        artifact_label="generated simulation sandbox"
    )

    assert "generated simulation sandbox" in prompt
    for forbidden in (
        "coverage",
        "conformal",
        "fdr",
        "benjamini",
        "true_ate",
        "oracle_effect",
    ):
        assert forbidden not in prompt.lower()

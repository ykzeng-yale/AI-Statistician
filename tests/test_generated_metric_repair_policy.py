from __future__ import annotations

from ai_statistician.generated_metric_repair_policy import (
    generated_coverage_metric_component_feedback,
    generated_metric_gate_repair_instruction,
)


def test_metric_gate_repair_instruction_preserves_coverage_target() -> None:
    prompt = generated_metric_gate_repair_instruction(
        artifact_label="generated algorithm draft"
    )

    assert "Do not lower target_coverage" in prompt
    assert "relax the acceptance gate" in prompt
    assert "not as strings" in prompt
    assert "sandbox_failed must be a boolean" in prompt
    assert "conservative finite-sample quantile/radius margin" in prompt
    assert "vacuous all-covering" in prompt


def test_component_coverage_feedback_requires_margin_without_vacuous_repair() -> None:
    prompt = generated_coverage_metric_component_feedback(
        artifact_label="generated simulation sandbox",
        target_coverage=0.9,
        return_fields=("empirical_coverage", "target_coverage", "mean_width"),
    )

    assert "return empirical_coverage >= 0.9" in prompt
    assert "Do not lower target_coverage" in prompt
    assert "not stringified numbers or booleans" in prompt
    assert "sandbox_failed must be a boolean" in prompt
    assert "local stochastic check clears the stated target" in prompt
    assert "without becoming vacuous" in prompt

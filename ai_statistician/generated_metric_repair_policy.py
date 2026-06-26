from __future__ import annotations

from typing import Sequence


GENERATED_METRIC_REPAIR_POLICY_NOT_PROOF_EVIDENCE = (
    "GENERATED_METRIC_REPAIR_POLICY_NOT_PROOF_EVIDENCE"
)


def generated_metric_gate_repair_instruction(*, artifact_label: str) -> str:
    """Shared prompt policy for generated-code metric gate repairs.

    This intentionally stays domain-neutral. Task-family packs may provide
    targets such as coverage, bias, or RMSE; the core coding-agent prompt should
    ask the model to repair the statistical calculation and utility tradeoff,
    not teach a benchmark-specific shortcut.
    """

    label = artifact_label.strip() or "generated draft"
    return (
        "Runtime metric-gate repair is active: the previous "
        f"{label} executed locally but returned statistically invalid metrics. "
        "Repair the estimator, DGP, uncertainty calculation, or metric computation "
        "so named probability/coverage metrics are nondegenerate, inside [0,1], "
        "and satisfy the stated target when target_coverage is present. Do not "
        "only rename metrics or hide the coverage field. Do not satisfy the gate "
        "with a vacuous all-covering or otherwise utility-free output; preserve "
        "and return relevant utility diagnostics such as mean_width, interval_size, "
        "bias, RMSE, efficiency, or failure_rate when the task calls for them. "
        "If the safe subset cannot express a statistically meaningful repair, "
        "omit the generated draft and record the needed registered adapter or "
        "human-reviewed implementation blocker instead. "
    )


def generated_coverage_metric_component_feedback(
    *,
    artifact_label: str,
    target_coverage: float,
    return_fields: Sequence[str],
) -> str:
    """Component-eval feedback for a prior zero-coverage generated draft."""

    label = artifact_label.strip() or "generated Python sandbox"
    fields = ", ".join(
        str(field).strip() for field in return_fields if str(field).strip()
    )
    field_sentence = f" Return {fields}." if fields else ""
    return (
        f"Repair the {label}. The previous draft executed but reported zero "
        f"coverage; return empirical_coverage >= {target_coverage}. The repair "
        "must come from a statistically meaningful DGP, estimator, uncertainty, "
        "or coverage computation, not from renaming metrics, hiding the coverage "
        "field, or returning a vacuous all-covering output. Preserve utility "
        "diagnostics such as mean_width, interval_size, bias, RMSE, efficiency, "
        "or failure_rate when relevant so the eval can detect coverage-utility "
        "tradeoffs."
        + field_sentence
    )

from __future__ import annotations

from typing import Any

from .research_schema import ResearchReport


class DefaultTheoryDeveloper:
    """Conservative theory-side repair agent for simulation failures.

    This handler does not freely invent a new statistical paper. It converts a
    failed simulator diagnosis into a scoped theory-revision artifact: which
    procedure/theorem component should change, which assumptions changed, what
    formal obligations become next, and what simulation improvement is expected.
    A separate application layer is still required before the coordinator can
    rerun with the revised method.
    """

    def repair_theory_issue(
        self,
        item: dict[str, Any],
        report: ResearchReport,
    ) -> dict[str, Any] | None:
        failed_diagnostics = tuple(str(row) for row in item.get("failed_diagnostics", []) or [])
        target_procedure = str(item.get("target_procedure", "")) or _first_procedure_id(report)
        if not target_procedure:
            return None
        metric_evidence = _metric_evidence_for_item(item, report, target_procedure)
        revision = _revision_from_diagnostics(
            failed_diagnostics=failed_diagnostics,
            metric_evidence=metric_evidence,
            target_procedure=target_procedure,
            report=report,
        )
        return {
            "execution_status": "EXECUTED_SCOPED_THEORY_REVISION_PROPOSAL",
            "task_type": "theory_revision_from_simulation_failure",
            "result": (
                "Default TheoryDeveloper produced a scoped revision artifact from simulation feedback. "
                "It is a theory repair proposal; applying it to the planner/algorithm registry is a separate step."
            ),
            "rerun_requested": False,
            "repair_artifact": revision,
            "theory_developer_scope": "simulation-diagnosis-to-theory-revision",
        }


def _first_procedure_id(report: ResearchReport) -> str:
    return report.procedures[0].id if report.procedures else ""


def _metric_evidence_for_item(
    item: dict[str, Any],
    report: ResearchReport,
    target_procedure: str,
) -> dict[str, float]:
    key_filter = {str(row) for row in item.get("metric_evidence_keys", []) or [] if str(row)}
    for simulation in report.simulations:
        if simulation.procedure_id != target_procedure:
            continue
        diagnosis = simulation.diagnosis
        if diagnosis is not None and diagnosis.metric_evidence:
            return {
                str(key): float(value)
                for key, value in diagnosis.metric_evidence.items()
                if not key_filter or str(key) in key_filter
            }
        return {
            str(key): float(value)
            for key, value in simulation.metrics.items()
            if isinstance(value, (int, float)) and (not key_filter or str(key) in key_filter)
        }
    return {}


def _revision_from_diagnostics(
    *,
    failed_diagnostics: tuple[str, ...],
    metric_evidence: dict[str, float],
    target_procedure: str,
    report: ResearchReport,
) -> dict[str, Any]:
    diagnostic_text = " ".join(failed_diagnostics).lower()
    theorem_goals = _current_theorem_goal_ids(report)
    if any(token in diagnostic_text for token in ("coverage", "confidence", "calibration", "se")):
        return _coverage_revision(target_procedure, theorem_goals, failed_diagnostics, metric_evidence)
    if "bias" in diagnostic_text or "identification" in diagnostic_text:
        return _bias_revision(target_procedure, theorem_goals, failed_diagnostics, metric_evidence)
    if any(token in diagnostic_text for token in ("power", "fdr", "type_i", "optional")):
        return _testing_revision(target_procedure, theorem_goals, failed_diagnostics, metric_evidence)
    return _generic_revision(target_procedure, theorem_goals, failed_diagnostics, metric_evidence)


def _coverage_revision(
    target_procedure: str,
    theorem_goals: tuple[str, ...],
    failed_diagnostics: tuple[str, ...],
    metric_evidence: dict[str, float],
) -> dict[str, Any]:
    return {
        "revised_procedure": f"{target_procedure}:calibrated_interval_variant",
        "revised_theorem_goals": [
            *_suffix_goals(theorem_goals, "coverage_calibration"),
            "coverage_lower_bound_under_declared_dgp",
            "standard_error_or_quantile_calibration",
        ],
        "assumption_delta": [
            "make coverage theorem conditional on the simulator-declared DGP and stress-test regime",
            "separate point-estimator consistency from interval-calibration assumptions",
        ],
        "expected_simulation_delta": (
            "coverage diagnostics should move toward the declared nominal level without changing the target estimand"
        ),
        "failure_class": "coverage_or_standard_error_failure",
        "failed_diagnostics": list(failed_diagnostics),
        "metric_evidence": metric_evidence,
        "next_formal_obligations": [
            "miscoverage_event_equivalence",
            "coverage_lower_bound_of_complement_error",
            "variance_or_quantile_estimator_calibration",
        ],
    }


def _bias_revision(
    target_procedure: str,
    theorem_goals: tuple[str, ...],
    failed_diagnostics: tuple[str, ...],
    metric_evidence: dict[str, float],
) -> dict[str, Any]:
    return {
        "revised_procedure": f"{target_procedure}:bias_corrected_or_reidentified_variant",
        "revised_theorem_goals": [
            *_suffix_goals(theorem_goals, "identification_bias_control"),
            "identification_under_explicit_assumptions",
            "bias_decomposition_and_correction",
        ],
        "assumption_delta": [
            "add explicit identification conditions for the target estimand",
            "state whether observed bias is estimator bias, target mismatch, or DGP misspecification",
        ],
        "expected_simulation_delta": (
            "bias and relative-bias diagnostics should shrink while RMSE does not materially increase"
        ),
        "failure_class": "bias_or_identification_failure",
        "failed_diagnostics": list(failed_diagnostics),
        "metric_evidence": metric_evidence,
        "next_formal_obligations": [
            "unbiasedness_or_identification_bridge",
            "bias_decomposition_identity",
            "target_estimand_equivalence_under_assumptions",
        ],
    }


def _testing_revision(
    target_procedure: str,
    theorem_goals: tuple[str, ...],
    failed_diagnostics: tuple[str, ...],
    metric_evidence: dict[str, float],
) -> dict[str, Any]:
    return {
        "revised_procedure": f"{target_procedure}:error_rate_calibrated_variant",
        "revised_theorem_goals": [
            *_suffix_goals(theorem_goals, "error_rate_control"),
            "finite_sample_or_asymptotic_error_rate_control",
            "power_or_detection_boundary_under_stress_tests",
        ],
        "assumption_delta": [
            "state the null/alternative regime used by the simulator",
            "separate nominal error control from power or regret diagnostics",
        ],
        "expected_simulation_delta": (
            "FDR/type-I/optional-stopping diagnostics should satisfy the declared threshold while preserving power"
        ),
        "failure_class": "testing_error_rate_failure",
        "failed_diagnostics": list(failed_diagnostics),
        "metric_evidence": metric_evidence,
        "next_formal_obligations": [
            "event_error_bound_to_error_rate_control",
            "union_or_stopping_bound_bridge",
            "power_monotonicity_under_signal_strength",
        ],
    }


def _generic_revision(
    target_procedure: str,
    theorem_goals: tuple[str, ...],
    failed_diagnostics: tuple[str, ...],
    metric_evidence: dict[str, float],
) -> dict[str, Any]:
    return {
        "revised_procedure": f"{target_procedure}:diagnostic_revised_variant",
        "revised_theorem_goals": [
            *_suffix_goals(theorem_goals, "diagnostic_alignment"),
            "diagnostic_failure_decomposition",
            "revised_acceptance_rule_under_declared_dgp",
        ],
        "assumption_delta": [
            "make the theorem/simulation acceptance rule explicit for the failed diagnostic",
            "identify whether the failure is theory, implementation, or simulator-environment driven",
        ],
        "expected_simulation_delta": "the same simulator diagnostic should no longer fail after applying the revision",
        "failure_class": "generic_theory_or_procedure_failure",
        "failed_diagnostics": list(failed_diagnostics),
        "metric_evidence": metric_evidence,
        "next_formal_obligations": [
            "diagnostic_event_formalization",
            "acceptance_rule_soundness",
        ],
    }


def _current_theorem_goal_ids(report: ResearchReport) -> tuple[str, ...]:
    if isinstance(report.theorem_goals, dict):
        return tuple(str(key) for key in report.theorem_goals)
    return tuple()


def _suffix_goals(goals: tuple[str, ...], suffix: str) -> list[str]:
    selected = list(goals[:3])
    if not selected:
        return []
    return [f"{goal}:{suffix}" for goal in selected]


def theory_developer_fingerprint() -> str:
    return repr(
        {
            "handler": "DefaultTheoryDeveloper",
            "scope": "simulation-diagnosis-to-scoped-theory-revision",
            "repair_fields": [
                "revised_procedure",
                "revised_theorem_goals",
                "assumption_delta",
                "expected_simulation_delta",
            ],
        }
    )

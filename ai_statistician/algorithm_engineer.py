from __future__ import annotations

import math
from typing import Any

from .research_schema import CandidateProcedure, ResearchReport, ResearchSimulation


class DefaultAlgorithmEngineer:
    """Conservative algorithm-side repair agent for numerical failures.

    This handler does not execute arbitrary generated code. It converts
    implementation/numerical simulator diagnoses into a scoped repair artifact:
    which registered implementation failed, which finite/numerical guard should
    be added, what reproduces the failure, and what metrics must improve before
    the patch can be promoted.
    """

    def repair_algorithm_issue(
        self,
        item: dict[str, Any],
        report: ResearchReport,
    ) -> dict[str, Any] | None:
        target_procedure = str(item.get("target_procedure", ""))
        procedure = _procedure_for_target(report, target_procedure)
        if procedure is None:
            return None
        simulation = _simulation_for_procedure(report, procedure.id)
        metrics = dict(simulation.metrics) if simulation is not None else {}
        nonfinite_metrics = sorted(
            key
            for key, value in metrics.items()
            if isinstance(value, (int, float)) and not math.isfinite(float(value))
        )
        n_failed = float(metrics.get("n_failed", 0.0)) if isinstance(metrics.get("n_failed"), (int, float)) else 0.0
        n_runs = float(metrics.get("n_runs", 0.0)) if isinstance(metrics.get("n_runs"), (int, float)) else 0.0
        algorithm_spec = procedure.algorithm_spec
        implementation_hash = algorithm_spec.implementation_hash if algorithm_spec is not None else ""
        artifact = {
            "target_procedure": procedure.id,
            "algorithm_id": procedure.algorithm,
            "patch_summary": _patch_summary(nonfinite_metrics, n_failed=n_failed, n_runs=n_runs),
            "implementation_hash": implementation_hash,
            "reproduction_test": {
                "procedure_id": procedure.id,
                "failed_diagnostics": list(item.get("failed_diagnostics", []) or []),
                "failed_stress_tests": list(item.get("failed_stress_tests", []) or []),
                "metric_evidence_keys": list(item.get("metric_evidence_keys", []) or []),
                "observed_metrics": {
                    key: float(value)
                    for key, value in metrics.items()
                    if isinstance(value, (int, float)) and math.isfinite(float(value))
                },
                "nonfinite_metrics": nonfinite_metrics,
            },
            "rerun_metrics": {
                "n_failed_target": 0.0,
                "finite_metric_required": 1.0,
                "max_failed_fraction": 0.05,
                "original_n_failed": n_failed,
                "original_n_runs": n_runs,
            },
            "numerical_repair_kind": _repair_kind(nonfinite_metrics, n_failed=n_failed, n_runs=n_runs),
            "algorithm_registry_status": algorithm_spec.registry_status if algorithm_spec else "missing",
        }
        return {
            "execution_status": "EXECUTED_SCOPED_ALGORITHM_REPAIR_PROPOSAL",
            "task_type": "algorithm_repair_from_numerical_failure",
            "result": (
                "Default AlgorithmEngineer produced a scoped numerical repair artifact. "
                "It documents the implementation hash and rerun gates; it does not execute arbitrary generated code."
            ),
            "rerun_requested": False,
            "repair_artifact": artifact,
            "algorithm_engineer_scope": "diagnosis-to-repair-contract",
        }


def _procedure_for_target(report: ResearchReport, target_procedure: str) -> CandidateProcedure | None:
    if target_procedure:
        for procedure in report.procedures:
            if procedure.id == target_procedure:
                return procedure
    return report.procedures[0] if len(report.procedures) == 1 else None


def _simulation_for_procedure(report: ResearchReport, procedure_id: str) -> ResearchSimulation | None:
    for simulation in report.simulations:
        if simulation.procedure_id == procedure_id:
            return simulation
    return None


def _repair_kind(nonfinite_metrics: list[str], *, n_failed: float, n_runs: float) -> str:
    if nonfinite_metrics:
        return "finite_metric_guard"
    if n_runs > 0.0 and n_failed / n_runs > 0.10:
        return "replicate_failure_rate_reduction"
    return "numerical_stability_guard"


def _patch_summary(nonfinite_metrics: list[str], *, n_failed: float, n_runs: float) -> str:
    if nonfinite_metrics:
        return (
            "Add finite-value guards for simulator metrics "
            f"{', '.join(nonfinite_metrics)} and rerun the algorithm audit before promotion."
        )
    if n_runs > 0.0 and n_failed / n_runs > 0.10:
        return (
            "Reduce failed Monte Carlo replicate rate by adding deterministic numerical guards, "
            "bounded denominators, or explicit unsupported-replicate accounting before statistical diagnosis."
        )
    return "Add a targeted numerical-stability guard and rerun finite simulation diagnostics before promotion."


def algorithm_engineer_fingerprint() -> str:
    return repr(
        {
            "handler": "DefaultAlgorithmEngineer",
            "scope": "implementation-diagnosis-to-scoped-repair-artifact",
            "repair_fields": [
                "patch_summary",
                "implementation_hash",
                "reproduction_test",
                "rerun_metrics",
            ],
        }
    )

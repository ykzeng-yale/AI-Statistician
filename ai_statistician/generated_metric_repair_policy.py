from __future__ import annotations

from typing import Any, Mapping, Sequence


GENERATED_METRIC_REPAIR_POLICY_NOT_PROOF_EVIDENCE = (
    "GENERATED_METRIC_REPAIR_POLICY_NOT_PROOF_EVIDENCE"
)
GENERATED_COVERAGE_METRIC_CONTRACT_FIELDS: tuple[str, ...] = (
    "acceptance_gate",
    "acceptance_gates",
    "evaluation_metrics",
    "expected_metrics",
    "expected_outputs",
    "metric_contract",
    "metric_names",
    "required_metrics",
    "simulation_targets",
    "success_criteria",
    "target_metrics",
    "validation_metrics",
    "validation_metric_names",
)
GENERATED_COVERAGE_METRIC_EXPLICIT_FLAG_FIELDS: tuple[str, ...] = (
    "coverage_metric_required",
    "requires_coverage_metric",
)
GENERATED_COVERAGE_METRIC_EXPLICIT_TARGET_FIELDS: tuple[str, ...] = (
    "coverage_target",
    "nominal_coverage",
    "required_coverage",
    "target_coverage",
)
GENERATED_COVERAGE_METRIC_REQUIRED_ERROR = (
    "coverage metric required by generated sandbox metric policy"
)
GENERATED_METRIC_AUXILIARY_NAMES: tuple[str, ...] = (
    "alpha",
    "n",
    "n_cal",
    "n_calibration",
    "nominal",
    "nominal_alpha",
    "nominal_coverage",
    "nominal_level",
    "se",
    "sd",
    "stderr",
    "std",
    "standard_error",
    "target",
    "target_coverage",
)
GENERATED_METRIC_AUXILIARY_SUFFIXES: tuple[str, ...] = (
    "_se",
    "_sd",
    "_std",
    "_stderr",
)
GENERATED_SIMULATION_ORACLE_TRUTH_NAMES: tuple[str, ...] = (
    "oracle_ate",
    "oracle_effect",
    "target_ate",
    "target_effect",
    "true_ate",
    "true_effect",
)
GENERATED_SIMULATION_ORACLE_TRUTH_HARDCODED_ERROR = (
    "generated simulation oracle truth appears hard-coded while the DGP "
    "defines sample-level potential outcomes; compute true_ate/true_effect "
    "from the simulated mu1/mu0 or a matching closed-form DGP before "
    "coverage/bias metrics"
)


def generated_coverage_metric_required_error() -> str:
    return GENERATED_COVERAGE_METRIC_REQUIRED_ERROR


def generated_sandbox_requires_coverage_metric(context: Mapping[str, Any]) -> bool:
    """Return whether policy expects a named coverage metric.

    Coverage is a typed metric requirement, not a keyword inferred from the
    entire research blackboard. In particular, source-inventory
    ``coverage_status`` and prose such as ``assumption coverage`` must not alter
    an executable simulation's acceptance contract.
    """

    if not isinstance(context, Mapping):
        return False
    stack: list[Any] = [context]
    while stack:
        item = stack.pop()
        if isinstance(item, Mapping):
            for raw_key, value in item.items():
                key = str(raw_key or "").strip().lower().replace("-", "_")
                if key in GENERATED_COVERAGE_METRIC_EXPLICIT_FLAG_FIELDS:
                    if value is True or str(value or "").strip().lower() in {
                        "1",
                        "true",
                        "yes",
                    }:
                        return True
                elif key in GENERATED_COVERAGE_METRIC_EXPLICIT_TARGET_FIELDS:
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        return True
                elif key in GENERATED_COVERAGE_METRIC_CONTRACT_FIELDS:
                    if _coverage_metric_contract_value_requires_metric(value):
                        return True
                if isinstance(value, (Mapping, list, tuple)):
                    stack.append(value)
        elif isinstance(item, (list, tuple)):
            stack.extend(item)
    return False


def _coverage_metric_contract_value_requires_metric(value: Any) -> bool:
    stack: list[Any] = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, Mapping):
            stack.extend(item.values())
            continue
        if isinstance(item, (list, tuple)):
            stack.extend(item)
            continue
        text = str(item or "").strip().lower().replace("_", " ").replace("-", " ")
        if not text:
            continue
        if text in {"coverage", "miscoverage", "empirical coverage", "ci coverage"}:
            return True
        if any(
            phrase in text
            for phrase in (
                "coverage >=",
                "coverage >",
                "coverage at least",
                "coverage must",
                "coverage probability",
                "coverage rate",
                "empirical coverage",
                "interval coverage",
                "miscoverage",
                "prediction set coverage",
                "prediction interval coverage",
            )
        ):
            return True
        if "%" in text and "coverage" in text:
            return True
    return False


def is_generated_metric_auxiliary_name(name: str) -> bool:
    lowered = str(name or "").strip().lower()
    normalized = lowered.replace("-", "_").replace(" ", "_")
    if normalized in GENERATED_METRIC_AUXILIARY_NAMES:
        return True
    return normalized.endswith(GENERATED_METRIC_AUXILIARY_SUFFIXES)


def generated_simulation_oracle_truth_names() -> tuple[str, ...]:
    return GENERATED_SIMULATION_ORACLE_TRUTH_NAMES


def generated_simulation_oracle_truth_hardcoded_error() -> str:
    return GENERATED_SIMULATION_ORACLE_TRUTH_HARDCODED_ERROR


def generated_python_sandbox_safe_subset_contract() -> dict[str, object]:
    """Shared generated-Python contract exposed to coding-agent prompts."""

    return {
        "allowed_modules": ["math", "statistics", "random"],
        "allowed_import_forms": [
            "import math",
            "import statistics",
            "import random",
        ],
        "allowed_globals": [
            "abs",
            "all",
            "any",
            "bool",
            "dict",
            "enumerate",
            "float",
            "int",
            "len",
            "list",
            "max",
            "min",
            "pow",
            "range",
            "round",
            "set",
            "sorted",
            "str",
            "sum",
            "tuple",
            "zip",
        ],
        "allowed_methods": [
            "public methods on sandbox-local list/dict/set/tuple values",
            "public methods on objects returned by allowed modules",
            "math.*",
            "statistics.*",
            "random.*",
        ],
        "forbidden_import_forms": [
            "from math import ...",
            "from statistics import ...",
            "from random import ...",
            "bare helper aliases such as mean(), stdev(), sqrt()",
        ],
        "manual_summary_patterns": [
            "average = sum(values) / len(values) when values is non-empty",
            "variance = sum((x - average) ** 2 for x in values) / max(1, len(values) - 1)",
            "standard_error = math.sqrt(max(variance, 0.0) / n)",
        ],
        "forbidden_dependencies": [
            "numpy",
            "scipy",
            "sklearn",
            "pandas",
            "statsmodels",
            "torch",
            "jax",
        ],
        "forbidden_syntax": [
            "imports except math/statistics/random",
            "class definitions",
            "with blocks",
            "global/nonlocal",
            "file I/O, network, subprocess, eval, exec",
            "private/dunder names or attributes",
            "frame-reflection attributes such as generator/frame builtin or globals access",
            "reflective string formatting methods such as str.format/format_map",
            "rebinding protected sandbox callables or module names",
            "from-imported helper aliases; use plain module imports and module-qualified calls",
            "private/dunder method calls or attribute access",
        ],
        "result_contract": (
            "run_sandbox must return a JSON-serializable dict with string keys "
            "and finite scalar/list/dict metric values"
        ),
        "safe_random_usage": (
            "Use local RNG objects such as rng = random.Random(seed + rep); "
            "keep mutable state inside run_sandbox and do not use global/nonlocal."
        ),
        "fallback_rule": (
            "If the draft cannot be expressed in this pure-Python safe subset, "
            "omit the generated draft and record the required registered adapter "
            "or human-reviewed implementation blocker instead."
        ),
        "boundary": (
            "This contract describes the local generated-Python sandbox API only. "
            "Passing it is implementation evidence, not theorem proof evidence."
        ),
    }


def generated_python_sandbox_guard_repair_instruction(*, artifact_label: str) -> str:
    """Prompt repair instruction for drafts rejected by the static guard."""

    label = artifact_label.strip() or "generated Python sandbox draft"
    return (
        f"Generated-Python sandbox guard repair is active for the {label}: "
        "the next draft must keep all mutable state local to run_sandbox, avoid "
        "global/nonlocal, avoid classes/with/file/network/subprocess/eval/exec, "
        "and use only plain module imports: import math, import statistics, or "
        "import random. Do not write from statistics import mean/stdev or call "
        "bare helper aliases such as mean(), stdev(), or sqrt(); use "
        "sum(values) / len(values), explicit variance/std loops, or "
        "module-qualified calls such as statistics.mean(values), "
        "statistics.stdev(values), and math.sqrt(x). For stochastic simulations, "
        "prefer local RNG objects such as rng = random.Random(seed + rep) and "
        "use its public methods. Public operations on sandbox-local lists, dicts, "
        "sets, tuples, and allowed-module objects are available; private/dunder "
        "attributes, frame-reflection access, protected-name rebinding, and "
        "reflective str.format/format_map calls remain forbidden. "
        "Return a JSON-serializable dict with string "
        "keys and finite scalar/list/dict metric values. "
        "Do not hand-roll closure-based RNG state that requires nonlocal. "
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
        "Read the previous metric_gate_errors, metrics, metric_gate_targets, "
        "and code_excerpt as the concrete repair target. "
        "Repair the estimator, DGP, uncertainty calculation, or metric computation "
        "so named probability/coverage metrics are nondegenerate, inside [0,1], "
        "and satisfy the stated target when target_coverage is present. If an "
        "interval or prediction-set coverage metric is below target_coverage, "
        "the next draft must correct the coverage indicator and recalibrate the "
        "uncertainty radius/quantile enough to meet the target while still "
        "reporting utility diagnostics. Do not lower target_coverage, relax the "
        "acceptance gate, or replace the required coverage metric with an easier "
        "proxy. Return metric values as real int/float/bool values in the Python "
        "dict, not as strings; for example empirical_coverage and target_coverage "
        "must be numeric and sandbox_failed must be a boolean. When the prior "
        "coverage is close to but below target, repair with "
        "a conservative finite-sample quantile/radius margin so stochastic "
        "evaluation clears the stated target rather than landing on a knife-edge. "
        "If bias, RMSE, or a point-estimate error "
        "metric is large, first repair target/DGP/estimator alignment and the "
        "estimand used by the coverage indicator; do not merely widen intervals "
        "around a wrong center. For generated simulation stress tests, compute "
        "the oracle truth from the DGP used in that replicate, from explicit "
        "potential-outcome quantities, or from a closed-form derivation that "
        "matches the DGP; do not hard-code true_ate/true_effect/target values "
        "unless that derivation is actually consistent with the simulated "
        "outcome regressions. Do not only rename metrics or hide the coverage "
        "field. Do not satisfy the gate "
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
        "or coverage computation. For interval or prediction-set coverage, "
        "correct the coverage indicator and increase or recalibrate the "
        "uncertainty radius/quantile enough to meet target_coverage while still "
        "reporting utility diagnostics. Do not lower target_coverage, relax the "
        "acceptance gate, or report an easier proxy metric. Return metric values "
        "as int/float/bool values in the Python dict, not stringified numbers or "
        "booleans; empirical_coverage and target_coverage must be numeric and "
        "sandbox_failed must be a boolean. If empirical coverage "
        "is near but below target, add a conservative finite-sample margin to the "
        "quantile/radius so the next local stochastic check clears the stated "
        "target without becoming vacuous. Do not repair by renaming metrics, hiding the coverage "
        "field, or returning a vacuous all-covering output. Preserve utility "
        "diagnostics such as mean_width, interval_size, bias, RMSE, efficiency, "
        "or failure_rate when relevant so the eval can detect coverage-utility "
        "tradeoffs."
        + field_sentence
    )

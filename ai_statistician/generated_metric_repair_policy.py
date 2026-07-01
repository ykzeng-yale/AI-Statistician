from __future__ import annotations

from typing import Sequence


GENERATED_METRIC_REPAIR_POLICY_NOT_PROOF_EVIDENCE = (
    "GENERATED_METRIC_REPAIR_POLICY_NOT_PROOF_EVIDENCE"
)


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
            "list.append",
            "list.extend",
            "list.sort",
            "random.Random",
            "rng.random",
            "rng.uniform",
            "rng.gauss",
            "rng.normalvariate",
            "rng.shuffle",
            "math.*",
            "statistics.*",
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
            "from-imported helper aliases; use plain module imports and module-qualified calls",
            "method calls or attribute access outside math/statistics/random, rng random/shuffle methods, and list append/extend/sort",
        ],
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
        "call rng.random(), rng.uniform(), rng.gauss(), rng.normalvariate(), or "
        "rng.shuffle(local_list). Use sandbox-local collection operations such "
        "as values.append(value), values.extend(more_values), any(flags), and "
        "all(flags). "
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
        "reporting utility diagnostics. If bias, RMSE, or a point-estimate error "
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
        "reporting utility diagnostics. Do not repair by renaming metrics, hiding the coverage "
        "field, or returning a vacuous all-covering output. Preserve utility "
        "diagnostics such as mean_width, interval_size, bias, RMSE, efficiency, "
        "or failure_rate when relevant so the eval can detect coverage-utility "
        "tradeoffs."
        + field_sentence
    )

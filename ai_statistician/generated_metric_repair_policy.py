from __future__ import annotations

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
    """Shared domain-neutral prompt policy for typed metric-contract repairs."""

    label = artifact_label.strip() or "generated draft"
    return (
        "Runtime metric-gate repair is active: the previous "
        f"{label} executed locally but failed its pre-execution metric contract. "
        "Read metric_contracts, metric_contract_evaluation, metric_gate_errors, "
        "metrics, and code_excerpt as the exact repair target. Keep every "
        "contract_id, requirement_id, artifact_id, metric_path, and binding unchanged. "
        "Treat the runtime-materialized metric semantics, measurement protocol, "
        "operator, threshold/lower/upper, tolerance, aggregation/quorum, required "
        "flag and source anchors immutable, and keep authority lineage unchanged. "
        "Repair the generated estimator, simulation, DGP, or metric calculation "
        "so the declared result path exists, resolves to finite numeric values, "
        "and satisfies the recorded comparison. Do not rename the required result "
        "path, lower or remove a threshold, increase tolerance, change aggregation "
        "or quorum, make a required contract optional, invent a new required gate, "
        "or substitute an easier proxy. Return "
        "metric values as real int/float/bool/list/dict values rather than strings. "
        "For identity/mean/min/max, runtime aggregates raw values before applying "
        "the comparison. For all/any/at_least_count/at_least_fraction, runtime "
        "compares each raw value before applying the boolean aggregation or quorum. "
        "Return raw numeric measurements when they exist; do not pre-threshold them "
        "into 0/1 flags, and never compare those flags against a quorum count. Only "
        "an intrinsically boolean predicate should return bool/0/1, bound with "
        "operator == and threshold 1. "
        "Preserve all requested diagnostics needed to interpret the accepted "
        "result. If the safe subset cannot express a meaningful repair, omit the "
        "generated draft and record the required registered adapter or "
        "human-reviewed implementation blocker instead. Passing this contract is "
        "empirical execution evidence only and never theorem proof evidence. "
    )

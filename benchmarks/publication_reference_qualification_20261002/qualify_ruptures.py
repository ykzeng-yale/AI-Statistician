"""Evaluator-side finite reference inspection; no model or product imports."""

import argparse
import builtins
from collections import Counter
from fractions import Fraction
import hashlib
from importlib.metadata import distributions, version
from itertools import combinations, product
import json
import math
from pathlib import Path
import platform
import random
import subprocess
import sys

import numpy as np
from ruptures.costs import CostL2
from ruptures.detection import Dynp
from ruptures import exceptions


SEED = 20261002


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def segment_cost(rows, start, end):
    # Direct rational deviations, independent of NumPy variance and the DP.
    total = Fraction(0)
    for coordinate in zip(*rows[start:end]):
        mean = Fraction(sum(coordinate), end - start)
        total += sum((Fraction(value) - mean) ** 2 for value in coordinate)
    return total


def enumerate_partitions(n, changes, minimum, jump, costs):
    values = {}
    for interior in combinations(range(jump, n, jump), changes):
        ends = interior + (n,)
        starts = (0,) + interior
        if all(end - start >= minimum for start, end in zip(starts, ends)):
            values[ends] = sum(costs[start, end] for start, end in zip(starts, ends))
    return values


def datasets():
    rng = random.Random(SEED)
    for n, dimension in product((4, 5, 7, 8, 10, 12), (1, 2, 3)):
        for pattern in ("constant", "step", "alternating", "integer_noise"):
            rows = []
            for index in range(n):
                if pattern == "constant":
                    row = [coordinate - 2 for coordinate in range(dimension)]
                elif pattern == "step":
                    row = [(coordinate + 1) * (0 if index < n // 2 else 3)
                           for coordinate in range(dimension)]
                elif pattern == "alternating":
                    row = [(-1) ** (index + coordinate) * (coordinate + 1)
                           for coordinate in range(dimension)]
                else:
                    row = [rng.randint(-5, 5) for _ in range(dimension)]
                rows.append(row)
            yield f"n{n}_d{dimension}_{pattern}", rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--package-directory", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--cost-min-size", type=int, required=True)
    parser.add_argument("--infeasible-errors", nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    actual_commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    assert actual_commit == args.expected_commit
    assert version("ruptures") == args.expected_version
    assert CostL2().min_size == args.cost_min_size
    assert not subprocess.check_output(["git", "-C", str(source), "diff", "HEAD"], text=True)
    installed_root = Path(sys.modules["ruptures"].__file__).resolve().parent
    source_hashes = {relative: sha256(source / args.package_directory / relative)
                     for relative in ("detection/dynp.py", "costs/costl2.py", "utils/utils.py")}
    for relative, expected in source_hashes.items():
        assert sha256(installed_root / relative) == expected
    error_types = vars(builtins) | vars(exceptions)
    expected_errors = tuple(error_types[name] for name in args.infeasible_errors)
    assert all(issubclass(item, Exception) for item in expected_errors)

    inputs, rows_out, segment_checks, invariances = [], [], 0, []
    counts = Counter()
    grid_witness = None
    for identifier, rows in datasets():
        inputs.append({"id": identifier, "rows": rows})
        n = len(rows)
        signal = np.array(rows, dtype=float)
        cost = CostL2().fit(signal)
        costs = {(start, end): segment_cost(rows, start, end)
                 for start in range(n) for end in range(start + args.cost_min_size, n + 1)}
        for (start, end), exact in costs.items():
            assert math.isclose(cost.error(start, end), float(exact), rel_tol=1e-10, abs_tol=1e-10)
            segment_checks += 1

        for requested_minimum, jump, changes in product((1, 2, 3, 4), (1, 2, 3, 5), range(4)):
            minimum = max(args.cost_min_size, requested_minimum)
            partitions = enumerate_partitions(n, changes, minimum, jump, costs)
            result = {"input": identifier, "requested_min_size": requested_minimum,
                      "effective_min_size": minimum, "jump": jump, "changes": changes,
                      "admissible_partitions": len(partitions)}
            algorithm = Dynp(model="l2", min_size=requested_minimum, jump=jump).fit(signal)
            try:
                returned = tuple(algorithm.predict(changes))
            except expected_errors as error:
                result.update(exception=type(error).__name__, message=str(error))
                result["status"] = "infeasible_rejected" if not partitions else "feasible_failed"
            except Exception as error:
                result.update(status="unexpected_exception", exception=type(error).__name__, message=str(error))
            else:
                result["returned_endpoints"] = returned
                if not partitions:
                    result["status"] = "infeasible_returned"
                else:
                    optimum = min(partitions.values())
                    optimizers = [ends for ends, value in partitions.items() if value == optimum]
                    result.update(exact_optimum=str(optimum), optimal_partition_count=len(optimizers))
                    result["status"] = "exact_optimum" if returned in optimizers else "nonoptimal_or_invalid"
                    if returned in partitions:
                        result["exact_returned_objective"] = str(partitions[returned])
            counts[result["status"]] += 1
            rows_out.append(result)

        full = enumerate_partitions(n, 1, 2, 1, costs)
        grid = enumerate_partitions(n, 1, 2, 5, costs)
        if grid_witness is None and grid and min(full.values()) < min(grid.values()):
            grid_witness = {"input": identifier, "rows": rows,
                            "full_grid_objective": str(min(full.values())),
                            "jump_5_objective": str(min(grid.values()))}
        optimizers = {ends for ends, value in full.items() if value == min(full.values())}
        for scale, shift in ((1, 11), (3, 0)):
            transformed = [[scale * value + shift * (coordinate + 1)
                            for coordinate, value in enumerate(row)] for row in rows]
            assert segment_cost(transformed, 0, n) == scale ** 2 * costs[0, n]
            check = {"input": identifier, "scale": scale, "shift_multiplier": shift}
            try:
                returned = tuple(Dynp(model="l2", min_size=2, jump=1).fit_predict(
                    np.array(transformed, dtype=float), n_bkps=1
                ))
            except Exception as error:
                check.update(status="failed", exception=type(error).__name__, message=str(error))
            else:
                check.update(status="passed" if returned in optimizers else "failed",
                             returned_endpoints=returned)
            invariances.append(check)

    successful_statuses = {"exact_optimum", "infeasible_rejected"}
    summary = {
        "scope": "finite_evaluator_reference_inspection_not_agent_evaluation",
        "source_commit": actual_commit, "source_hashes": source_hashes,
        "package_directory": args.package_directory, "cost_min_size": args.cost_min_size,
        "expected_infeasible_errors": args.infeasible_errors,
        "installed_source_path": str(installed_root),
        "runtime": sys.version, "platform": platform.platform(),
        "packages": dict(sorted((item.metadata["Name"], item.version) for item in distributions())),
        "seed": SEED, "datasets": len(inputs), "configurations": len(rows_out),
        "status_counts": dict(counts), "segment_cost_checks": segment_checks,
        "translation_and_scaling_checks": len(invariances),
        "translation_and_scaling_status_counts": dict(Counter(item["status"] for item in invariances)),
        "float_cost_tolerance": {"absolute": 1e-10, "relative": 1e-10},
        "optimality_acceptance": "Exact rational objective of returned admissible partition; any exact tie accepted.",
        "all_configurations_matched": set(counts) <= successful_statuses
                                      and all(item["status"] == "passed" for item in invariances),
        "default_grid_loss_witness": grid_witness,
        "model_calls": 0, "study_activated": False,
        "independent_full_task_gold_qualified": False,
    }
    for name, value in (("inputs.json", inputs), ("cases.json", rows_out),
                        ("invariances.json", invariances), ("summary.json", summary)):
        (args.output_dir / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["all_configurations_matched"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

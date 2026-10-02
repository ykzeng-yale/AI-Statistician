"""Pre-inference numerical cross-check with the unchanged pinned author package."""

import argparse
import hashlib
from importlib.metadata import version
from itertools import product
import json
from pathlib import Path
import subprocess

import numpy as np
import ruptures
from ruptures.exceptions import BadSegmentationParameters

from benchmarks.publication_development.fixed_k_l2_20261002 import numerical_evaluator as oracle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    pin = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.source, text=True).strip()
    assert pin == "a3f8c437edf7d54c1a8f90aaa72638363a011765" and version("ruptures") == "1.1.10"
    assert ruptures.costs.CostL2().min_size == 1
    counts = {"matched_feasible": 0, "matched_infeasible": 0}
    for request in oracle.requests(730109):
        values = oracle.partition_values(request["signal"], request["n_changes"], request["min_size"], request["jump"])
        model = ruptures.Dynp(model="l2", min_size=request["min_size"], jump=request["jump"]).fit(np.array(request["signal"]))
        try:
            ends = model.predict(n_bkps=request["n_changes"])
        except BadSegmentationParameters:
            assert not values
            counts["matched_infeasible"] += 1
        else:
            assert values and tuple(ends) in values and values[tuple(ends)] == min(values.values())
            assert np.isclose(model.cost.sum_of_costs(ends), float(min(values.values())), rtol=1e-10, atol=1e-10)
            counts["matched_feasible"] += 1
    law = oracle.finite_experiment_values()
    for noises, expected in zip(product((-1, 1), repeat=6), law):
        signal = np.array([[mean + noise] for mean, noise in zip((0, 0, 0, 1, 1, 1), noises)])
        model = ruptures.Dynp(model="l2", min_size=2, jump=1).fit(signal)
        assert np.isclose(model.cost.sum_of_costs(model.predict(n_bkps=1)), float(expected), rtol=1e-10, atol=1e-10)
    result = {"author_pin": pin, "package_version": version("ruptures"), "numpy_version": version("numpy"),
              "oracle_sha256": hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
              "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "request_seed": 730109,
              **counts, "matched_finite_experiment_cases": len(law), "exact_experiment_mean": str(sum(law) / 64),
              "scope": "finite_numerical_author_cross_check_not_mathematical_or_full_task_qualification"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == "__main__":
    main()

"""Cross-check the numerical oracle before any product research inference."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from benchmarks.publication_development.curvature_iv_20261002.numerical_evaluator import exact_reference, requests


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    support = np.arange(-2.0, 3.0)
    design = np.column_stack((np.ones(5), support))
    coefficients = np.linalg.lstsq(design, support ** 2, rcond=None)[0]
    residual = support ** 2 - design @ coefficients
    assert np.allclose(residual, [-0.0 + 2, -1, -2, -1, 2], rtol=0, atol=1e-14)
    cases = zero_cases = 0
    for request in requests(730219):
        expected = exact_reference(request)
        z, d, y = (np.asarray(request[key], dtype=float) for key in ("z", "d", "y"))
        # This path uses a fitted finite-support population projection and a
        # scalar linear solve, independently of the oracle's rational sums.
        w = residual[(z + 2).astype(int)]
        denominator = float(w @ d / len(z))
        assert abs(denominator - expected["moment_denominator"]) < 1e-12
        if expected["status"] == "zero_moment":
            assert abs(denominator) < 1e-12
            zero_cases += 1
        else:
            beta = float(np.linalg.solve(np.array([[w @ d]]), np.array([w @ y]))[0])
            score = w * (y - beta * d)
            se = float(np.linalg.norm(score) / abs(w @ d))
            assert np.isclose(beta, expected["beta"], rtol=1e-10, atol=1e-10)
            assert np.isclose(se, expected["standard_error"], rtol=1e-10, atol=1e-10)
        cases += 1
    here = Path(__file__).resolve().parent
    result = {"numerical_cases": cases, "zero_moment_cases": zero_cases,
              "oracle_sha256": hashlib.sha256((here / "numerical_evaluator.py").read_bytes()).hexdigest(),
              "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "numpy_version": np.__version__, "mathematical_authority_qualified": False,
              "scope": "independent_numerical_implementation_check_not_general_theory_acceptance"}
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))


if __name__ == "__main__":
    main()

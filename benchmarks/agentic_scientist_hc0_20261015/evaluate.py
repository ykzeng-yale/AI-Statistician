"""Public numerical agreement check, not a mathematical or research certificate."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import traceback

import numpy as np
import statsmodels.api as sm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    output = Path(args.results_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    error = None
    try:
        path = Path(args.program_path).resolve()
        sys.path.insert(0, str(path.parent))
        spec = importlib.util.spec_from_file_location("candidate", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for index, (n, p) in enumerate(((40, 2), (80, 3), (120, 5), (60, 2), (100, 3), (160, 5))):
            rng = np.random.default_rng(2026101500 + index)
            x = np.column_stack((np.ones(n), rng.normal(size=(n, p - 1))))
            y = x @ np.linspace(-0.5, 1.0, p) + (0.5 + np.abs(x[:, 1])) * rng.normal(size=n)
            reference = sm.OLS(y, x).fit(cov_type="HC0")
            observed = module.run_estimator({"design_matrix": x.tolist(), "outcomes": y.tolist()})
            checks = {}
            for key, expected in (("coefficients", reference.params),
                                  ("covariance", reference.cov_params()),
                                  ("standard_errors", reference.bse)):
                actual = np.asarray(observed[key], dtype=float)
                checks[key] = bool(actual.shape == expected.shape and np.all(np.isfinite(actual))
                                   and np.allclose(actual, expected, rtol=1e-6, atol=1e-9))
            rows.append({"case": index, "n": n, "p": p, "checks": checks, "passed": all(checks.values())})
    except Exception:
        error = traceback.format_exc()
        print(error, file=sys.stderr)
    passed = sum(row["passed"] for row in rows)
    metrics = {"combined_score": passed / 6, "public": {"passed": passed, "total": 6},
               "scope": "numerical implementation agreement only", "cases": rows, "error": error}
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (output / "correct.json").write_text(json.dumps({"correct": passed == 6 and error is None,
        "message": "Numerical agreement is not theory or research acceptance.", "error": error}, indent=2) + "\n")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()

"""Operator launcher for unchanged statsmodels GEE code and its upstream test."""

import hashlib
import json
from pathlib import Path

import numpy as np
import statsmodels
from statsmodels.genmod import cov_struct, families
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.tests.test_gee import TestGEE, load_data


def main():
    package = Path(statsmodels.__file__).resolve().parent
    root = Path(__file__).resolve().parent
    source_hashes = {}
    for relative in (
        "genmod/generalized_estimating_equations.py",
        "genmod/cov_struct.py",
        "genmod/tests/test_gee.py",
        "genmod/tests/results/gee_poisson_1.csv",
    ):
        installed = (package / relative).read_bytes()
        assert installed == (root / "statsmodels" / relative).read_bytes(), relative
        source_hashes[relative] = hashlib.sha256(installed).hexdigest()

    TestGEE().test_poisson()
    y, x, groups = load_data("gee_poisson_1.csv")
    fits = []
    for covariance in (cov_struct.Independence(), cov_struct.Exchangeable()):
        model = GEE(y, x, groups, family=families.Poisson(), cov_struct=covariance)
        result = model.fit()
        fits.append({
            "working_correlation": type(covariance).__name__,
            "converged": bool(result.converged),
            "coefficients": result.params.tolist(),
            "robust_standard_errors": result.bse.tolist(),
            "working_dependence_parameter": np.asarray(covariance.dep_params).tolist(),
        })
    output = {
        "upstream_test": "statsmodels.genmod.tests.test_gee.TestGEE.test_poisson",
        "upstream_test_passed": True,
        "source_hashes": source_hashes,
        "observations": len(y),
        "clusters": len(np.unique(groups)),
        "regression_columns": x.shape[1],
        "fits": fits,
        "scope": "Pinned public implementation and stored R comparisons; not a new R execution or a replication of the 1986 paper experiments.",
    }
    Path("gee_source_result.json").write_text(json.dumps(output, indent=2) + "\n")
    print("Upstream GEE Poisson test passed; two fitted models written to gee_source_result.json.")


if __name__ == "__main__":
    main()

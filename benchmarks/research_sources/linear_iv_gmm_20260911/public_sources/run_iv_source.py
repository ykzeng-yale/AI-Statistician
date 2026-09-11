"""Operator launcher for unchanged upstream code; not a generated estimator."""

import hashlib
import json
from pathlib import Path

import linearmodels
from linearmodels.tests.iv import test_gmm
from linearmodels.tests.iv._utility import generate_data


root = Path(__file__).resolve().parent
installed = Path(linearmodels.__file__).resolve().parent
for name in (
    "iv/model.py", "iv/gmm.py", "iv/covariance.py", "tests/iv/test_gmm.py",
    "tests/iv/_utility.py", "datasets/meps/meps.csv.bz2", "datasets/meps/__init__.py",
):
    assert (installed / name).read_bytes() == (root / "linearmodels" / name).read_bytes(), name

tests = [test_gmm.test_heteroskedastic_center, test_gmm.test_heteroskedastic_debiased,
         test_gmm.test_heteroskedastic_config]
for test in tests:
    test(generate_data())
    print("UPSTREAM_TEST_PASSED", test.__name__)

notebook = json.loads((root / "examples/iv_advanced-examples.ipynb").read_text())
cells = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
namespace = {}
for index, source in enumerate(cells[:11]):
    exec(compile(source, f"upstream_notebook_code_cell_{index}", "exec"), namespace)
result = namespace["res_gmm"]
print(result.summary)
print(result.j_stat)
output = {
    "package_version": linearmodels.__version__, "notebook_code_cells": list(range(11)),
    "upstream_tests": [test.__name__ for test in tests],
    "sample_size": int(result.nobs), "coefficient_order": list(result.params.index),
    "coefficients": result.params.tolist(), "standard_errors": result.std_errors.tolist(),
    "covariance": result.cov.to_numpy().tolist(), "j_statistic": float(result.j_stat.stat),
    "j_degrees_of_freedom": int(result.j_stat.df), "j_pvalue": float(result.j_stat.pval),
    "covariance_type": result.cov_type, "iterations": int(result.iterations),
    "data_sha256": hashlib.sha256((installed / "datasets/meps/meps.csv.bz2").read_bytes()).hexdigest(),
    "scope": "First eleven code cells through two-step robust IVGMM, plus three unchanged weight-matrix tests. Not clustered/CUE/LIML or the complete notebook, not Hansen's original experiments, and not evidence of valid empirical instruments.",
}
Path("iv_source_result.json").write_text(json.dumps(output, indent=2) + "\n")

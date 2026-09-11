"""Operator launcher for unchanged, byte-verified statsmodels source tests."""

import hashlib
import json
from pathlib import Path

import numpy as np
import statsmodels
from statsmodels.regression.quantile_regression import QuantReg
from statsmodels.regression.tests.test_quantile_regression import (
    TestEpanechnikovHsheatherQ75,
    test_fitted_residuals,
)


def main():
    root = Path(__file__).resolve().parent
    package = Path(statsmodels.__file__).resolve().parent
    hashes = {}
    for relative in (
        'regression/quantile_regression.py',
        'regression/tests/test_quantile_regression.py',
        'regression/tests/results/results_quantile_regression.py',
        'datasets/engel/engel.csv',
    ):
        installed = (package / relative).read_bytes()
        assert installed == (root / 'statsmodels' / relative).read_bytes(), relative
        hashes[relative] = hashlib.sha256(installed).hexdigest()
    test_fitted_residuals()
    TestEpanechnikovHsheatherQ75.setup_class()
    test = TestEpanechnikovHsheatherQ75()
    names = sorted(name for name in dir(test) if name.startswith('test_'))
    for name in names:
        getattr(test, name)()
    data = statsmodels.datasets.engel.load_pandas().data
    X = np.column_stack([np.ones(len(data)), data.income])
    result = QuantReg(data.foodexp, X).fit(
        q=.75, vcov='iid', kernel='epa', bandwidth='hsheather',
    )
    output = {
        'source_hashes': hashes,
        'passed_tests': ['test_fitted_residuals', *names],
        'observations': len(data), 'coefficient_order': ['intercept', 'income'],
        'quantile': .75, 'vcov': 'iid', 'kernel': 'epa', 'bandwidth_method': 'hsheather',
        'coefficients': np.asarray(result.params).tolist(),
        'standard_errors': np.asarray(result.bse).tolist(),
        'bandwidth': float(result.bandwidth), 'sparsity': float(result.sparsity),
        'iterations': int(result.iterations),
        'scope': 'Pinned upstream implementation and stored R/Stata comparisons, not a fresh R run, new-estimator validation or original-paper experiment replication.',
    }
    Path('quantile_source_result.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Twelve upstream quantile-regression tests passed; Engel fit written to quantile_source_result.json.')


if __name__ == '__main__':
    main()

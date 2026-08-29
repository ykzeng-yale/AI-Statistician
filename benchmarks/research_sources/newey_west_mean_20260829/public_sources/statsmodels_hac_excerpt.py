"""Pinned public implementation excerpt used as model-visible research context.

Source:
https://github.com/statsmodels/statsmodels/blob/b24082f15d7603ffb250c282f34df7df3db10cb2/statsmodels/stats/sandwich_covariance.py

Upstream project: statsmodels
Pinned commit: b24082f15d7603ffb250c282f34df7df3db10cb2
License: BSD-3-Clause

This excerpt preserves the relevant public implementation convention. It is not
the benchmark estimator and is not hidden evaluation authority.
"""

import numpy as np


def weights_bartlett(nlags):
    """Return lag-zero through lag-nlags Bartlett weights."""
    return 1 - np.arange(nlags + 1) / (nlags + 1.0)


def S_hac_simple(x, nlags=None, weights_func=weights_bartlett):
    """Form the inner HAC covariance matrix for equally spaced observations."""
    if x.ndim == 1:
        x = x[:, None]
    n_periods = x.shape[0]
    if nlags is None:
        nlags = int(np.floor(4 * (n_periods / 100.0) ** (2.0 / 9.0)))
    weights = weights_func(nlags)

    S = weights[0] * np.dot(x.T, x)
    for lag in range(1, nlags + 1):
        s = np.dot(x[lag:].T, x[:-lag])
        S += weights[lag] * (s + s.T)
    return S


# In the full upstream file, cov_hac_simple obtains score-like rows xu, calls
# S_hac_simple, and sandwiches the result with an inverse Hessian. The focused
# benchmark instead applies the scalar Bartlett construction directly to the
# centered observations and divides by n when converting long-run variance to
# the variance estimate of the sample mean.

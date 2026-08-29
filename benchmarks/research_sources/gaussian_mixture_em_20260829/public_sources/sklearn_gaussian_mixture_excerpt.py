# Excerpt from scikit-learn, commit 88552088fad33d6ec70e1aaf633389d08fffb970.
# Source: sklearn/mixture/_gaussian_mixture.py. License: BSD-3-Clause.
# Copyright (c) 2007-2026 The scikit-learn developers.

def _estimate_gaussian_parameters(X, resp, reg_covar, covariance_type, xp=None):
    xp, _ = get_namespace(X, xp=xp)
    nk = xp.sum(resp, axis=0) + 10 * xp.finfo(resp.dtype).eps
    means = (resp.T @ X) / nk[:, xp.newaxis]
    covariances = {
        "full": _estimate_gaussian_covariances_full,
        "tied": _estimate_gaussian_covariances_tied,
        "diag": _estimate_gaussian_covariances_diag,
        "spherical": _estimate_gaussian_covariances_spherical,
    }[covariance_type](resp, X, nk, means, reg_covar, xp=xp)
    return nk, means, covariances


def _m_step(self, X, log_resp, xp=None):
    xp, _ = get_namespace(X, log_resp, xp=xp)
    self.weights_, self.means_, self.covariances_ = _estimate_gaussian_parameters(
        X, xp.exp(log_resp), self.reg_covar, self.covariance_type, xp=xp
    )
    self.weights_ /= xp.sum(self.weights_)
    self.precisions_cholesky_ = _compute_precision_cholesky(
        self.covariances_, self.covariance_type, xp=xp
    )

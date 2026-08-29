# Excerpt from scikit-learn, commit 88552088fad33d6ec70e1aaf633389d08fffb970.
# Source: sklearn/mixture/_base.py. License: BSD-3-Clause.
# Copyright (c) 2007-2026 The scikit-learn developers.

for n_iter in range(1, self.max_iter + 1):
    prev_lower_bound = lower_bound

    log_prob_norm, log_resp = self._e_step(X, xp=xp)
    self._m_step(X, log_resp, xp=xp)
    lower_bound = self._compute_lower_bound(log_resp, log_prob_norm)
    current_lower_bounds.append(lower_bound)

    change = lower_bound - prev_lower_bound
    if abs(change) < self.tol:
        converged = True
        break


def _e_step(self, X, xp=None):
    log_prob_norm, log_resp = self._estimate_log_prob_resp(X, xp=xp)
    return xp.mean(log_prob_norm), log_resp

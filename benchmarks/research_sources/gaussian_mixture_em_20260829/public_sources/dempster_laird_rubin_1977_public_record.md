# Public record: EM likelihood monotonicity

## Primary result

- A. P. Dempster, N. M. Laird, and D. B. Rubin.
- *Maximum Likelihood from Incomplete Data via the EM Algorithm*.
- Journal of the Royal Statistical Society, Series B 39(1):1-38, 1977.
- DOI: https://doi.org/10.1111/j.2517-6161.1977.tb01600.x

The paper presents the expectation-maximization algorithm for incomplete-data
likelihood problems and derives monotone likelihood behavior. Finite-mixture
models are among its examples. The focused benchmark asks for a self-contained
specialization to a two-component univariate Gaussian mixture with one known
common standard deviation.

## Focused model

The component label is latent. The mixing weight and two component means are
unknown, while the common positive standard deviation is fixed and known. The
task requires the posterior-responsibility E step, the exact closed-form M step,
and a Jensen or lower-bound/KL proof that each exact cycle weakly increases the
observed likelihood.

Monotone likelihood does not imply that every initialization reaches a global
maximum. Mixture labels are nonidentifiable without a naming convention, and
additional regularity is needed for stronger claims about parameter-sequence
convergence. The benchmark uses deterministic mean ordering only to make the
executable response label-invariant.

## Open-source implementation context

- Project: scikit-learn
- Repository: https://github.com/scikit-learn/scikit-learn
- Commit: 88552088fad33d6ec70e1aaf633389d08fffb970
- License: BSD-3-Clause
- Relevant source:
  - `sklearn/mixture/_base.py`
  - `sklearn/mixture/_gaussian_mixture.py`

The pinned excerpts show a mature E-step/M-step iteration and responsibility-
weighted Gaussian parameter updates. scikit-learn implements a more general
model and estimates covariance parameters; it is public implementation context,
not the required known-variance ABI, hidden expected output, or proof evidence.

# Fixed Quantile-Regression Source

The executable source is statsmodels 0.14.6 at commit
`40e6a84d26ac74623c6b94b718f0987ef0351c53`, under its BSD-3-Clause license.
The snapshot contains unchanged quantile-regression source, tests, stored result
arrays, Engel data and a public example. The operator launcher checks installed
source/data bytes against the snapshot, calls the unchanged upstream tests, and
records the fitted Engel-data coefficients and uncertainty. The environment lock
describes the actual current isolated environment, not historical author hardware.

The fitted-residual test compares against stored R quantreg values. The other
selected tests compare a 0.75 quantile fit using the iid covariance mode against
stored Stata results. Neither comparison executes R or Stata now. This is a
software-source reproduction, not recreation of every published experiment.
The new research estimator and its conditional-density covariance are separate
model-authored artifacts that require their own review and experiments.

## Literature

- Koenker and Bassett (1978), *Regression Quantiles*, Econometrica 46(1), 33-50,
  [DOI](https://doi.org/10.2307/1913643). The paper develops regression quantiles
  and joint asymptotics under a common error distribution.
- Knight (1998), *Limiting Distributions for L1 Regression Estimators under General
  Conditions*, Annals of Statistics 26(2), 755-770,
  [DOI](https://doi.org/10.1214/aos/1028144858). It develops a convex local-objective
  approach and considers error laws without the usual positive derivative.

Selected original pages were inspected during operator preparation. Copyrighted
paper scans are not redistributed in this public snapshot. These citations do not
license silently applying a common-error theorem to a different heteroskedastic
model. The candidate must state and justify the conditions for its claimed result.

The private evaluator reference, reference implementation, controls, hidden cases,
seeds and acceptance tolerances are absent from this snapshot.

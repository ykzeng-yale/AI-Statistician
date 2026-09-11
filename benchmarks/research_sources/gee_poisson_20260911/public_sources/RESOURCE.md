# GEE Source Scope

This snapshot contains unmodified code, test data, tests and documentation from
statsmodels 0.14.6, commit `40e6a84d26ac74623c6b94b718f0987ef0351c53`.
The BSD license is included. The operator launcher checks installed files against
the snapshot, executes the original `TestGEE.test_poisson`, and reports fits using
independence and estimated exchangeable working correlation. That upstream test
compares coefficients and robust standard errors with stored R `gee` results.
It does not execute R in this environment.

Liang and Zeger, *Longitudinal data analysis using generalized linear models*,
Biometrika 73(1), 13-22 (1986), DOI
[10.1093/biomet/73.1.13](https://doi.org/10.1093/biomet/73.1.13), is the original
method reference. Its publisher abstract describes regression estimating
equations for correlated longitudinal responses without specifying their joint
distribution. The accessible implementation documents its relation to that work.
The institutional full-text URL returned HTTP 403 during preparation; full paper
text and original 1986 experiment outputs are not included or claimed reproduced.

The new research task studies a specified fixed-working-correlation Poisson GEE.
Its estimator is not identical to the source test's estimated-correlation fit.
Explain that distinction and cite exact inspected code or output. Neither this
resource descriptor nor successful source execution proves asymptotic theory,
validates model-authored code, or replaces frozen confirmatory experiments.

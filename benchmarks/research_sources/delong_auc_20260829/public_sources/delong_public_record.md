# Public record: DeLong AUC variance

## Primary result

- Elizabeth R. DeLong, David M. DeLong, and Daniel L. Clarke-Pearson.
- *Comparing the Areas under Two or More Correlated Receiver Operating
  Characteristic Curves: A Nonparametric Approach*.
- Biometrics 44(3):837-845, 1988.
- DOI: https://doi.org/10.2307/2531595

The paper develops a nonparametric covariance estimator for empirical ROC areas
from generalized U-statistic structural components. Task 95 uses the single-curve
variance specialization only; it does not ask for the correlated-curve comparison.

## Fast structural-component formulation

- Xu Sun and Weichao Xu.
- *Fast Implementation of DeLong's Algorithm for Comparing the Areas Under
  Correlated Receiver Operating Characteristic Curves*.
- IEEE Signal Processing Letters 21(11):1389-1393, 2014.
- DOI: https://doi.org/10.1109/LSP.2014.2337313
- Author manuscript: https://pamixsun.github.io/papers/sun2014fast.pdf

This source states the midrank/Heaviside structural-component formulation and
shows how sorting reduces placement computation from quadratic to linearithmic
time. Runtime correctness in this task is defined by the public ABI, not by a
required implementation complexity.

## Open-source implementation

- Project: pROC
- Repository: https://github.com/xrobin/pROC
- Release: v1.19.1
- Commit: be0475b49cb353318703f9e48aa9eb9cd125d677
- License: GPL-3.0-or-later
- Relevant source:
  - `src/delong.cpp`
  - `R/delong.R`

The pinned excerpts expose the tie-aware placements and the single-AUC variance
calculation. They are implementation context, not hidden expected output and not
proof evidence.

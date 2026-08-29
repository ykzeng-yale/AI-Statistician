# Newey-West public record and task scope

## Bibliographic record

Whitney K. Newey and Kenneth D. West, "A Simple, Positive Semi-Definite,
Heteroskedasticity and Autocorrelation Consistent Covariance Matrix,"
Econometrica 55 (1987), 703-708, DOI 10.2307/1913610. An earlier public NBER
technical working paper is T0055, DOI 10.3386/t0055.

Public NBER metadata describes the contribution as a simple HAC covariance
construction that is positive semidefinite by construction and consistent under
general conditions. The journal result concerns covariance estimation for
dependent and potentially heteroskedastic observations; it does not make a
finite-sample exact-normality or unbiasedness claim.

## Focus of this benchmark

The benchmark specializes the general HAC idea to inference for the mean of one
equally spaced, covariance-stationary scalar time series. It uses centered sample
autocovariances with divisor n and the Bartlett lag window. The model must derive
the finite-n variance identity for the sample mean, distinguish the population
long-run variance from a truncated sample estimator, state sufficient asymptotic
conditions rather than claiming consistency from stationarity alone, and explain
why the Bartlett construction is nonnegative.

The source record is background evidence, not a proof. Exact public formulas,
input/output semantics, and empirical scope are frozen in the visible task
contract. Numerical experiments can test implementations and finite designs but
cannot prove the universal asymptotic result.

## Public links

- NBER record: https://www.nber.org/papers/t0055
- Journal DOI: https://doi.org/10.2307/1913610


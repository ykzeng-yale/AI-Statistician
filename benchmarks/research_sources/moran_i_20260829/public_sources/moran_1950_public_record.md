# Public record: Moran's I randomization expectation

## Primary result

- P. A. P. Moran.
- *Notes on Continuous Stochastic Phenomena*.
- Biometrika 37(1/2):17-23, 1950.
- DOI: https://doi.org/10.1093/biomet/37.1-2.17

The paper introduced the spatial autocorrelation statistic now called Moran's
I. The focused task uses the global statistic and its expectation under random
assignment of fixed observed values to fixed spatial sites. It does not ask for
analytic variance, a normal approximation, local indicators, or a spatial
stochastic-process model.

## Open-source implementation

- Project: PySAL esda
- Repository: https://github.com/pysal/esda
- Commit: dcd9c74bb2b78563c45d4f4a7977da9315d45c56
- License: BSD-3-Clause
- Relevant source:
  - `esda/moran.py`
  - `esda/tests/test_moran.py`

The pinned excerpts show the current global statistic normalization, the
reported randomization expectation, and public regression values. They are
implementation context, not hidden expected output and not proof evidence.

## Scope of the known result

For a fixed nonconstant vector and a fixed zero-diagonal weight matrix with
positive total weight, uniformly permuting the values over labeled sites gives
the conditional expectation -1/(n-1). The result follows from the centered
finite-population cross moment for two distinct sites. It does not require
Gaussian observations, symmetric weights, or row standardization.

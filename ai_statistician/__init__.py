"""Production-oriented AI statistician core.

The package separates:

- estimator theory selection,
- formal Lean proof obligations,
- algorithm implementation,
- Monte Carlo simulation feedback,
- trace persistence.
"""

from .system import AIStatisticianSystem

__all__ = ["AIStatisticianSystem"]


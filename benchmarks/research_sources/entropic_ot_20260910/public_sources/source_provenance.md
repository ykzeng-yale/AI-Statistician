# Public Source Scope

POT 0.9.6.post1 is pinned to `85113e9a380f5fcf684c50c73c1ff6a164a7366e`.
`plot_OT_1D.py`, `_sinkhorn.py`, and `LICENSE` are unchanged files from
[PythonOT/POT](https://github.com/PythonOT/POT/tree/85113e9a380f5fcf684c50c73c1ff6a164a7366e),
distributed under MIT. The example constructs two 100-bin histograms and compares
unregularized and regularized transport plans.

The operator launcher runs the complete unchanged example with the Agg plotting
backend, then exports its original `G0` and `Gs` arrays and numerical diagnostics.
It does not implement a transport solver. No figure is exported or visually
assessed, and no original hardware timing, historical environment, or complete
statistical-paper experiment reproduction is asserted. The frozen environment
is recorded in `environment_lock.json`.

## Literature

- Cuturi (2013), [Sinkhorn Distances](https://arxiv.org/abs/1306.0895).
- Bigot, Cazelles and Papadakis (2019), [Central limit theorems for
  entropy-regularized optimal transport on finite spaces and statistical
  applications](https://arxiv.org/abs/1711.08947v3), Electronic Journal of Statistics
  13(2), 5120-5150.
- Klatt, Tameling and Munk (2020), [Empirical Regularized Optimal Transport:
  Statistical Theory and Applications](https://arxiv.org/abs/1810.09880).

These works connect regularized transport optimization, differentiability and
sampling limits. The finite-support statistical results do not automatically
justify a shrinking regularization parameter, zero limiting variance, or an
uncentered Wald approximation for a different transport functional. Terminology
for regularized values and centered losses varies; identify the task's precise
objective rather than transferring a name. Source assistance is permitted, not
blind rediscovery. Full papers are linked, not redistributed here.

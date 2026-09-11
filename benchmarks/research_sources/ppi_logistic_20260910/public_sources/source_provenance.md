# PPI++ Logistic Source Snapshot

Primary paper: Angelopoulos, Duchi and Zrnic, *PPI++: Efficient
Prediction-Powered Inference*, arXiv:2311.01453v2 (2024-03-26),
https://arxiv.org/html/2311.01453v2 . Consult Sections 3, 4 and 6 and their proofs.

Official implementation: https://github.com/aangelopoulos/ppi_py at commit
`3d1f0c668444907b39bd045cb9dd38e479ce7dd6`, MIT license. The local snapshot's
`test_logistic.py` and `ppi.py` are exact upstream files, not model solutions.

`reproduce_logistic.py` is an operator-authored launcher. It calls the unchanged
`ppi_logistic_ci_subtest` 1000 times with its original default n=1000, N=10000,
d=1 and three error levels. Only reproducible per-replicate seeds and numeric
result export are added outside the helper. This is not the upstream ten-trial
parallel test and is not a recreation of every paper figure or historical hardware.
The original helper generates a new random coefficient and biased predictor each
trial; its data-generating mechanism differs from the new research study.

The environment lock records the newly prepared environment, not a claim that it
matches the authors' original installation. Source execution has no network,
inherited credentials or source edits. Read both actual streams and the declared
numeric result; report warnings and discrepancies without silently repairing them.

The public implementation supplies context and a separate baseline. The new
estimator must be model-authored from numerical primitives. Its frozen task uses
a label-only pilot for a single power-tuning step; upstream's default pilot uses
lambda=1. These finite-sample procedures must not be described as identical.
No reference theorem, hidden evaluation seeds or new-study outcomes are included.

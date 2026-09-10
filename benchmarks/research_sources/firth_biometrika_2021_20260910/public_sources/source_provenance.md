# Jeffreys-Penalized Logistic Regression: Public Sources

This snapshot contains public material for assisted known-result research. It is
not a blind rediscovery task or a source of independent hidden evaluator results.

Primary article: Kosmidis and Firth (2021), "Jeffreys-prior penalty, finiteness and
shrinkage in binomial-response generalized linear models", Biometrika 108(1),
71-82, DOI 10.1093/biomet/asaa052. The published article is CC BY 4.0.
`paper.txt` is extracted from the published PDF provided by Warwick WRAP.

The author-provided v1.4 supplementary archive is dated 23 March 2020 and is linked
from arXiv:1812.01938v4. Its R files explicitly state GPL 2 or greater. The
`jeffreys-MPL.R`, `sur-candes-2019.R`, and `README` files are unchanged author
source. `supplement.txt` is extracted from the supplied supplementary PDF. The
supplement lists R 3.6.3 and enrichwith 0.3.1 among its original dependencies.

`reproduce_coefficients.R` is an operator-authored launcher that invokes the
unchanged author function on the exact seed, design, and coefficient experiment
in `sur-candes-2019.R`, exporting the two coefficient vectors as a CSV. It does
not run the original 50-repeat timing experiment, reconstruct all figures, or
claim to reproduce the original hardware timings. No algorithm is reimplemented
in this launcher. The original script remains available for comparison.

The current environment uses R 4.4.3 and the original enrichwith 0.3.1 release.
The R version, operating system and numerical-library differences must remain
explicit. Source warnings and convergence information are observations for the
researcher to interpret, not evidence of correctness by themselves.

This public source experiment is exploratory replication evidence. It cannot
substitute for a newly derived mathematical argument, independent implementation,
fresh frozen confirmation, or Lean proof. The supplied source and paper may be
read and attributed. Hidden evaluator code, seeds, thresholds and outcomes are
not part of this snapshot.

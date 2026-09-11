# Source Scope

The public GP implementation and user-guide source are unmodified files from
scikit-learn commit `866c0f51e7560ef0303cbcc5f159df5382ea9e3f` (1.9.1), under
the included BSD 3-Clause license. `run_gp_source.py` is an operator-authored
launcher, not an upstream example or a model-authored estimator. It loads the
pinned local implementation and uses installed, version-bound numerical dependencies.

The mathematical reference is Rasmussen and Williams, *Gaussian Processes for
Machine Learning* (MIT Press, 2006), [Chapter 2](https://gaussianprocess.org/gpml/chapters/RW2.pdf).
The copyrighted book is not redistributed here. This source-assisted task is not
blind rederivation, original-figure replication, historical environment reproduction,
or a claim of novelty. Independent confirmation of new model-authored code is separate
from this source execution.

The launcher's two fixed designs use eight training and four distinct test locations,
known parameters and 1000 independent joint latent/noise draws per design. They
record latent and noisy marginal and joint coverage plus residual second moments.
These original outputs are observations, not pre-accepted theoretical conclusions.
Numerical conditioning of the fixed input matrices was checked before sampling;
no jitter, hyperparameter fitting or favorable-outcome stopping is used.

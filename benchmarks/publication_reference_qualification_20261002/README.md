# Published Reference Qualification

Started 2026-10-02 at product commit `33bc9747`. This is evaluator-side source
and environment preparation, not a product-agent run, an activated benchmark,
independent mathematical gold, or a publication result. No model is called.

The prospective papers need references that execute independently of candidate
outputs. A public repository, package test, or copied result table does not
establish that the original scientific claim is true. Keep source/environment
failures visible; do not repair author code and call it exact replication.
These sources do not replace the full matched-arm and independent-theory work.

## Source Selection

- RepliSims supplies human replication reports across several statistical domains,
  including unsuccessful replications. Its authors explicitly did not assess
  correctness of the original methods. Numerical replication authority and
  mathematical authority must remain separate. The inspected RepliSims code is
  a human reimplementation, not the original paper authors' simulation code.
- JSS supplies publication-linked Python/R source and replication archives.
  Qualify the published archive rather than silently substituting current GitHub
  HEAD. Exclude precomputed outputs from future author workspaces.
- DoubleML's JMLR 2022 paper was already consumed by the historical development
  ladder. A new software version does not make that family fresh; it is excluded
  from the prospective publication test pool.

Sources: [RepliSims](https://arxiv.org/abs/2307.02052),
[scikit-fda](https://www.jstatsoft.org/article/view/v109i02),
[bizicount](https://www.jstatsoft.org/article/view/v109i01).
The adjacent [source inventory](sources.json) records inspected versions and limits.
It is not a random or representative final task sample. No 24-family study,
test split, sampling plan, or agent efficacy experiment has been activated.

## scikit-fda Environment

The journal replication README requests Python 3.11, scikit-fda 0.9.1, and its
attached exact runtime requirements. Use a separate reference environment; do
not mutate the product `.venv`. A plain current isolated build of fdasrsf 2.5.8
failed with `Compiler.__init__() ... 4 were given` under current setuptools.
The build-only constraints in this directory record failed attempt 2. They
removed that compiler API error but the isolated build lacked SciPy and could
not find BLAS. A third attempt preinstalled pinned build dependencies and the
paper's SciPy, then disabled build isolation for fdasrsf only, as supported by
[uv](https://docs.astral.sh/uv/pip/compatibility/#pep-517-build-isolation).
It failed linking `cython_blas.cpython-311-darwin`. None is a qualified
installation recipe or recovered historical lock. The original algorithm and
replication script remain unchanged; the full script has not been executed.

Failed attempt 2, with paths selected by the evaluator:

```sh
uv venv --python 3.11 --managed-python "$REFERENCE_ENV"
uv pip install --python "$REFERENCE_ENV/bin/python" \
  --build-constraint scikit_fda_build_constraints.txt \
  -r "$REPLICATION/requirements.txt" "$SCIKIT_FDA_PACKAGE_ZIP"
```

The unchanged `v109i02.py` requests `../Figures`, downloads external datasets,
and runs a full classification search as well as visual examples. Supply the
directory and record fetched data identities; do not cut it down and label the
result a full-paper reproduction. A reference execution is not complete until
the actual process exits and outputs are inspected.

## Other Observations

Unchanged RepliSims Austin code was probed under native R 4.4.2 with a fixed seed. Its
continuous-outcome branch failed on undefined `lin_pred`; a mixed-covariate binary
branch failed with non-conformable arguments. The all-normal binary branch
returned 100 rows and binary outcomes/treatments. These are narrow source probes,
not the paper's complete simulation, a numerical gold comparison, or evidence
that every branch or the underlying statistical result is invalid. No author
source was patched.

The published bizicount package is 1.3.3 whereas the replication session reports
1.3.2. Several local dependencies are missing; no installation or execution was
attempted. Its archive includes cached simulation output, tables and figures,
which cannot substitute for fresh computation. Three additional RepliSims
repositories remain discovery-only: no clear code license was found in the
inspected root metadata, and their code was not executed or copied into this
repository. References alone do not qualify those candidates.

## Forward Evidence

Future author/evaluator processes must use separate workspaces. Hide reference
outputs, reports, cached tables and evaluator source where the track requires
blinding. Freeze the task and its scientifically justified numerical tolerance
before candidate calls. Pin environment adaptations and data snapshots equally
across comparison arms. References may qualify numerical agreement but cannot
accept a theory derivation. Official model runs use prospective open-weight
conditions only, and all consumed outcomes remain immutable.

The source inventory is a preparation record, not a new repair layer, task-family
instruction set or product dependency. It must stay outside any blinded author
workspace. No source here has yet qualified independent full-task gold.

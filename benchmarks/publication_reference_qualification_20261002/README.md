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

## bizicount Reference Execution

The journal package is 1.3.3; the author replication session used 1.3.2 and
R 4.3.3. A fresh execution used native R 4.4.2 on arm64 macOS, package 1.3.3
and recorded dependency versions. This is an adapted environment, not recovery
of the historical lock. The six executed author scripts match the archive bytes.
Only scripts and README were extracted: cached tables, figures and simulation
output were not copied into the new execution directory. The unchanged master
script ran all five stages, including all 4,000 simulation slots, and exited zero.
It reported 12.29 minutes for the Monte Carlo stage, not a controlled performance
measurement or an agent cost.

Environment preparation initially failed because the R 4.4 resolver did not
offer the needed `gsl` dependency. Its available native binary and the journal
package were installed in a separate reference library. The first master attempt
still failed before the empirical stage: this machine's `Rscript` wrapper resets
`R_LIBS_USER`, overriding the environment-only choice. The author installer then
changed the user-global R library. This side effect is retained and disclosed;
that attempt was not isolated. The second attempt explicitly prepended the
reference library with `.libPaths`, used a fresh output directory and completed.
The product `.venv` and author source were not changed. This is evaluator/operator
preparation, not evidence of product-agent dependency reconstruction.

Successful invocation, with evaluator-selected paths:

```sh
Rscript --vanilla -e '
  .libPaths(c(Sys.getenv("REFERENCE_R_LIBRARY"), .libPaths()))
  stopifnot(as.character(packageVersion("bizicount")) == "1.3.3",
            requireNamespace("copula", quietly = TRUE))
  print(sessionInfo())
  source("v109i01-replication.R", echo = TRUE)
'
```

Output inspection found 3,628 numeric results and 372 `NULL` returns. The two
high-zero-inflation scenarios retained only 300/500 and 354/500 rows; the other
six retained 490--499. The source conflates missing-zero and fit-error reasons
in `NULL`, and its plots drop those rows. Moreover, 842 numeric rows contain
bivariate optimizer code 3 in at least one fit. A numeric return is not a
successful-fit verdict; conditional performance cannot hide unconditional
failure counts. The full inspection includes all scenario counts, code pairs,
session versions and hashes. A first metadata export failed on the `sessionInfo`
S3 object; projecting plain session fields fixed export while reading the same
output, without rerunning the reference or scoring a candidate.

Fresh Table 3 mostly matches displayed coefficients and two-decimal likelihood
and information criteria, but several standard errors and a significance label
differ. For example, the ZIP zero-inflation intercept SE is 0.79 versus 1.08 in
the archive. The cause has not been isolated. Do not invent an explanation,
change a tolerance or label this exact full-table reproduction.

There is also a verified source issue in the pinned 1.3.3 package:
`R/bizicount.R:724` uses `log(length(y))` in BIC, where `y` is a two-column
`Formula::model.part` data frame and the observations number 312. Its length is
2; the package separately records `nrow(y)` as `nobs`. The BIC method returns
that stored value. Standard BIC uses `log(nobs)` in the penalty
([R documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/AIC.html)).
This was checked independently from the Formula return shape and unchanged
package source. It is not a claim about current versions, the entire paper's
theory, or a proven cause of the standard-error differences. No corrected value
from rounded likelihoods is supplied as gold. Source/output hashes and precise
boundaries are in the adjacent inventory; no author code was patched or vendored.

This source remains **unqualified as independent full-task gold**. A future task
could distinguish reproduction of specified software outputs from diagnosis of
scientific discrepancies, but its target and authority must be frozen before any
candidate call. A completed operator reference run is neither product autonomy
nor an official open-weight publication result.

## Other Observations

Unchanged RepliSims Austin code was probed under native R 4.4.2 with a fixed seed. Its
continuous-outcome branch failed on undefined `lin_pred`; a mixed-covariate binary
branch failed with non-conformable arguments. The all-normal binary branch
returned 100 rows and binary outcomes/treatments. These are narrow source probes,
not the paper's complete simulation, a numerical gold comparison, or evidence
that every branch or the underlying statistical result is invalid. No author
source was patched.

Three additional RepliSims
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

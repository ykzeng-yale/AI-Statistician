# Published Reference Qualification

Started 2026-10-02 at product commit `33bc9747`. This is evaluator-side source
and environment preparation, not a product-agent run, an activated benchmark,
independent mathematical gold, or a publication result. No model is called.

The prospective papers need references that execute independently of candidate
outputs. A public repository, package test, or copied result table does not
establish that the original scientific claim is true. Keep source/environment
failures visible; do not repair author code and call it exact replication.
These sources do not replace the full matched-arm and independent-theory work.
All qualification work below is separate from archived Haiku evaluations.

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
replication script remain unchanged; none of those attempts executed the full
script. The original source inventory preserves that preparation outcome. The
separately planned adapted follow-up below does not replace those failures.

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

### Adapted Follow-up

The separate [attempt 4 plan](scikit_fda_followup_plan.json) was committed at
`52becbeb`; [environment readiness](scikit_fda_followup_ready.json) was recorded
at `76c679d1` before the complete unchanged script ran. The exact fdasrsf 2.5.8
Python 3.11 Conda build requires NumPy 1.23.*, conflicting with the author's
1.26.4 pin. Its Python 3.12 build supports 1.26.*. This attempt used Python
3.12.2 and the latter unmodified binary, not a bypassed constraint, package
upgrade or patched source. All 36 author-listed runtime versions matched.
Conda initially installed Wheel 0.48.0, incompatible with packaging 23.2; only
that additional build tool changed to 0.42.0. The original failed dependency
check, install records and recipe remain available. The
[environment record](scikit_fda_followup_environment.json) distinguishes the
initial Conda transaction, later pip transactions and final distributions.

The first full script invocation used fresh output/data/home directories,
headless Agg and one BLAS/OpenMP thread. It completed in 58.72 seconds with exit
zero, created 14 single-page PDFs, and printed `0.879`, matching the displayed
classification value in Section 3.5 on page 27 of the
[paper](https://www.jstatsoft.org/index.php/jss/article/view/v109i02/4562).
All output pages were rendered/read; archive, data, source and output hashes
are retained in the [result record](scikit_fda_followup_results.json). The last
interactive example was constructed but GUI interaction was not tested.

This establishes a runnable published reference in an adapted environment and
one displayed numerical match. It does not qualify every figure, theoretical
claim or independent full-task gold, demonstrate product autonomy, or activate
a publication comparison. No model was called, no old candidate resubmitted,
and no source/results are inserted into product prompts or runtime rules.
Future replication tasks need prospectively fixed external checks that require
fresh computation, not simply the presence of copied output values/files.

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

## ebnm Published R Reference

The [ebnm paper](https://www.jstatsoft.org/article/view/v114i03) supplies a
GPL-3-or-later package and an explicitly MIT-licensed replication archive.
The [plan](ebnm_plan.json) was committed at `aa3981fb`; the adapted native
R 4.4.2 environment and 131 owned package identities were frozen at `46c9c476`
before science ran. The journal package is 1.1-38; cached author output records
R 4.3.2 and package 1.1-25. Neither current GitHub HEAD nor a patched author
script was substituted. Dependencies were installed only into the owned
reference library; the product environment and R global library were unchanged.
Preparation installed successfully but its evaluator version-string assertion
failed (`1.1.38` versus `1.1-38`). A separate readiness check used R's version
type without reinstalling or executing the science. The failed log is preserved.

The unchanged default `code.R` completed once with exit zero in 280.69 seconds.
It generated 900 timing rows and 300 simulation rows: three DGPs, ten prior
families and ten trials per cell. All 870 finite likelihood/RMSE/coverage cells
match the cached author run exactly; both retain the same 30 missing likelihoods.
The introductory displayed RMSE values also match. Five PDFs were rendered and
inspected; HTML numerical material was read but browser layout was not checked.
No cached output was copied into the fresh execution directory. The
[result](ebnm_results.json) records output, environment, script and log identities.

This is a runnable **numerical reproduction reference**, not independent theory
gold, full-paper replication, product autonomy or official agent efficacy.
The default excludes the author's two-day full timing option; the appendix
requires MOSEK and was not run. R summarized 46 deferred warnings without their
bodies, which were not serialized; this observation loss is disclosed, not
recovered by a rerun. The initial data inspection also emitted three namespace
warnings when loading saved closures without the owned library; only numeric
fields were inspected, and its original script/logs remain available. Future
inspector startup now binds that library; no existing inspection was overwritten.
Author code, numerical results and previously consumed evaluations were not fixed.

The particular paper is not in the inspected task records, but earlier
normal-means/conjugacy/Tweedie/James-Stein/SURE questions overlap its background.
It is not automatically an independent fresh theory family. Prospective task
grouping, concealed candidate checks and their scientific authority still need
to be fixed; published and cached values cannot alone certify fresh computation.

## TSCI Discovery Boundary

The [TSCI JSS paper](https://www.jstatsoft.org/article/view/v114i07) is a second
candidate, in invalid-instrument causal inference. Its journal package is 3.0.5,
GPL-3-or-later, archive SHA-256
`ba3e44efb4db449f6d7b6c26897d77d442a0c96a72d36e3dc32fe0e983b65b2b`.
The separate replication attachment is plain R source, not a ZIP; its SHA-256 is
`d3777089b2b947020e75ae185e8a47b43ca72d35770a074e2e46badb30e87113`.
It includes a seeded five-split boosting example and a user-supplied hat-matrix
example on the Card dataset. Methods Sections 2.1--2.4 and the package selection
implementation were inspected, but the source was not executed or vendored.
The script does not contain an asset-level license notice; journal policy alone
has not qualified redistribution of that separate attachment.

The [underlying theory record](https://arxiv.org/abs/2203.12808v4) changed title
and authors between versions. Match exact statement/assumption editions before
creating theory gold; invalid instruments do not mean identification without
restrictions. In particular, this is not just ordinary valid-IV GMM under a new
name. At that discovery checkpoint, no TSCI environment, independent theory rubric,
numerical reference or study split had been qualified. Both sources remain
preparation, not a new sampling frame selected on observed agent outcomes.

### TSCI Adapted Follow-up

The separate [plan](tsci_plan.json) was committed at `3f46fcd1`; adapted native
R 4.4.2 [readiness](tsci_ready.json) and the
[published displays](tsci_published_displays.json) were committed at `0dc3bc43`
before author science. The journal TSCI 3.0.5 source, XGBoost 1.7.7.1 and
fda 6.1.8 match the paper's computational versions. Rfast, ranger, MASS and
other recorded dependencies differ; this is not the historical R 4.3.1 environment.
All 65 prepared packages are in an owned library, and five fresh PSOCK workers
verified the six checked package locations/versions. Native-library contents are
also recorded; no user/site library or product environment was modified.

Preparation first stopped on one SSL download failure, then on relocated R's
absent system framework link path. The same frozen index and archive versions
were retained. Explicitly adding the existing local framework search path made
the unchanged sources install; failed logs remain available. This is operator
environment preparation, not autonomous product capability or a new repair layer.

The complete unchanged journal attachment ran once in a fresh directory and
exited zero in 39.41 seconds. Both printed estimation examples, selection/strength
statistics and B-spline head match paper pages 11--13 and 15 at displayed
precision. All 40 stored per-split coefficient/standard-error values are finite.
The four aggregate FWER standard-error NAs and the secondstage MSE NA remain
visible. All three parent warnings, including weak-IV non-testability, have their
messages and calls retained. Worker-local condition histories are not completely
exposed by the original code, so retained finite rows do not prove no internal
failed attempts. The [result record](tsci_results.json) binds source, environment,
logs, original data and stored-object inspection without rerunning the science.

One operator metadata mistake is preserved: the frozen display record inferred
secondstage `n_splits=1`, whereas the paper says no sample splitting and the
stored source uses 0. That file was not retrospectively fixed or labelled as
all-fields passing. No numerical tolerance was fitted after execution.

This qualifies a runnable numerical reference for the supplied attachment, not
full-paper replication, independent theory gold, a fresh independent family or
an official agent result. Card data do not supply a known causal truth, and
weak-IV non-testability is not evidence of instrument validity. Future family
grouping and external task checks remain unfrozen; attachment redistribution
rights remain unresolved. No model was called or historical evaluation revisited.

The subsequent [TSCI scientific-source review](tsci_scientific_source_review.md)
examines the final 2026 JMLR edition, selected proof dependencies and its separate
replication repository. It identifies localized written-algorithm/proof
inconsistencies and a different experiment scope; it does not invalidate or
upgrade the earlier attachment's numerical-reference result. No model or new
numerical experiment was run. TSCI is not yet a qualified publication case or
mathematical gold source.

## RepliSims Probes

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

## Fixed-K Segmentation Reference

The [ruptures inspection](ruptures_reference_notes.md) adds one published
methods/library source with independent exact finite numerical checks. Both
author implementations are post-publication pins, not a recovered historical
release. Unchanged 1.0.6 passed its 484 upstream tests but failed the independent
inspection; it remains unqualified. Separately pinned 1.1.10 passed 585 upstream
tests and the inspected admissible optimization cases. No author source was
patched and no source or paper was vendored. Environment adaptations and
failures remain explicit in the inventory.

The evaluator script is not a product tool, prompt recipe or hidden test set.
It enumerates finite partitions with rational arithmetic, not a second DP or
model referee. This is a narrow numerical reference, not an asymptotic result,
full-paper replication, independent full-task gold or agent success.

Use a separate CPython 3.11.15 environment and the adjacent version-pinned
requirements. Install the exact source checkout with `uv pip install --python
"$REFERENCE_ENV/bin/python" --no-build-isolation "$SOURCE"`. The 1.1.10 build
additionally uses `ruptures_v1_1_10_build_requirements.txt`. These are adapted
package/build pins, not wheel-hash locks or cross-platform qualification.

```sh
"$REFERENCE_ENV/bin/python" qualify_ruptures.py \
  --source-root "$SOURCE" --package-directory src/ruptures \
  --expected-commit a3f8c437edf7d54c1a8f90aaa72638363a011765 \
  --expected-version 1.1.10 --cost-min-size 1 \
  --infeasible-errors BadSegmentationParameters --output-dir "$FRESH_OUTPUT"
```

For the retained 1.0.6 source, explicitly use package-directory `ruptures`,
commit `f0399cfab733a319397f5fb3df9dd64edea5c40d`, version `1.0.6`, cost minimum
2 and errors `AssertionError NotEnoughPoints`. That reference inspection exits
nonzero; do not silently omit failing configurations or repair the optimizer.

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

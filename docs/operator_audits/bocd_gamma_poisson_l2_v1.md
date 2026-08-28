# BOCD Gamma-Poisson L2 v1 operator audit

## Immutable disposition

Task `bayesian_online_changepoint_gamma_poisson_paper_to_code` received one
fresh exact-`claude-haiku-4-5-20251001` product draw and one post-runtime hidden
evaluation. Both are consumed and immutable. Product research completion was
`0/1`, hidden full-task evaluation was `0/1`, and trusted full-task capability
remains `0/1`. Formalization was `not_applicable` and did not run.

The runtime ended `BLOCKED` at the terminal Critic after 13 traces, 11 outer
graph iterations, two same-owner scientific workspace continuations, 30 runtime
tool calls, 32 observations, and 12 handoffs. All seven enabled model roles used
exact Haiku. There were no Sonnet or Opus calls, provider fallback, model
escalation, second scheduler, or post-run source feedback.

## Mathematical finding

The persistent Markdown/LaTeX workspace is real and materially better than the
old JSON mathematics transport, but the accepted theory is internally
contradictory.

In `bocd_gamma_poisson_theory.md`, lines 21-34 correctly derive that a
Gamma(shape `a`, rate `b`) prior becomes `Gamma(a+x,b+1)` after one Poisson
count. Lines 215-230 later assert the incompatible update
`shape=a+r, rate=b+sum(x)` and explicitly propagate `shape` unchanged while
adding the count to `rate`. Line 63 also initializes the rate-like state to zero
despite the declared positive prior rate. These statements cannot all be true
under the document's own shape-rate predictive formula.

The independent referee repeated the same error. Its report lines 22-28 states
the correct predictive, while lines 73-81 endorses the reversed update. Lines
156-159 even states the correct required child `Gamma(shape+x,rate+1)` and then
marks the incompatible implementation verified. The referee's `ACCEPT` is
therefore not trustworthy mathematical evidence.

The frozen hidden theory harness reported 7/7 mechanical checks and the
calibrated Haiku semantic judge reported eight of eight claims satisfied. That
automated theory result is preserved but operator-invalidated for capability
attribution: a long document can contain a correct local statement and a later
active contradiction that the single semantic call overlooks despite a passed
activation near miss.

## Scientific-code finding

The committed estimator is causal, deterministic, normalized, stable on long
sequences, and preserves the constant-hazard row-zero identity. Those are useful
component observations, but they do not establish the core recursion.

In the generated estimator, lines 149-158 keep `nu` unchanged and update
`chi += x_t`, although the same source calls `nu` the Gamma shape and `chi` the
Gamma rate. Under its predictive formula, the growth child must update the
shape by the observed count and the rate by one. The hidden algorithm harness
executed 24 exact calls: causality, row-zero identity, determinism, and
long-sequence stability passed, while the public-contract aggregate, numerical
reference, invalid-count, and invalid-hyperparameter dimensions failed.

The independent code reviewer used three diagnostic attempts. Two failed before
invoking the estimator because the reviewer authored an invalid probe ABI. The
third invoked the exact estimator 12 times but checked only structure,
normalization, causality, MAP self-consistency, finite log evidence, and the
row-zero identity. It supplied no independently derived numerical oracle. Its
report lines 148-162 placed the observed and expected state updates beside each
other and still called them equivalent. It also claimed booleans were rejected,
although Python's `bool` passes the implementation's `int` checks.

## Empirical finding

The hidden empirical harness executed 4,001 exact estimator calls over the four
frozen designs and coal application. Invocation completion, replicate minimum,
design count, detection margin, and public coal-input identity passed. The
aggregate reference result, false-reset margin, and coal-output reference failed.
This is consistent with the wrong conjugate update, but hidden results generated
no runtime feedback and cannot be used to repair this consumed source.

The model-authored Simulation source reached executable checkpoints. The final
independent source review correctly rejected it for accepting fewer than 1,000
replicates and for defining but not executing the coal analysis. The intended
same-owner regeneration was then blocked before a model call because the task
carried both an old scientific-progress continuation and the new semantic-review
continuation. That is a shared lifecycle defect, not a BOCD content defect.

## Future-only mechanism response

Commit `b9297aef` makes one source-owner task carry exactly one continuation
mode. A semantic rejection now starts from the exact reviewed source and raw
findings while dropping stale progress/replay markers. It also clarifies the
existing reviewer probe's stable function signature and asks the same reviewer
model to compare load-bearing transitions side by side and attempt a
discriminating oracle before claiming numerical correctness. Runtime still
chooses no test case, formula, interpretation, edit, owner, retry, or acceptance
result.

No Task 76 artifact was rerun, resumed, repaired, hidden-evaluated again,
rescored, resampled, or exposed to hidden/operator findings. The result remains
`0/1`; aggregate trusted capability remains `4/76`.

Future-task regressions passed `161/161` for the affected shared surfaces and
`1001/1001` repository-wide in 81.48 seconds. Compileall, JSON, diff hygiene,
secret scanning, and the existing 150,000-line production budget passed at
149,993 lines. These checks confer no retrospective scientific credit.

## Evidence identity

- Runtime manifest SHA-256: `aac0161b23a95ae45ecf9eda588e6ba821dd2a59d593d98dcd8559503eefc279`
- Runtime result SHA-256: `daff9abbcab945d9866bd32b7bfd60860f250f58f9921f697466c82280e39791`
- Hidden evaluation SHA-256: `526a7f7390552c3e11122f296ef50fcc18d4c5390540b74b4d375323b780dd7e`
- Runtime topology SHA-256: `df1535027335b65267330d999873d065b2ede3ba1e53023e0db0f7cbaf304072`
- Theory document SHA-256: `3aebdad3438373dfcfadf994f3f184f68f3e9208a36e28727d0c0a299450ae27`
- Estimator document SHA-256: `df84254b72da2820f2b5020ec6494e30fb71e9d2beb01e4063b7d3b588b8335d`
- Referee report SHA-256: `ca352af1e7ba15122e4bc88fa3ca93abd848bbbc0dada9d02d9f5201bdea81f0`
- Evaluated estimator source identity: `fd0f3580421e3be4b9c7c1b8f2ead0a7a66e68dee54114b7ec56f5a223f0dfbe`
- Hidden theory result hash: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden theory semantic result hash: `02f1e6800ff72b9e2712b495df4628e990a185e2a35e8f62c7964ffa218939dd`
- Hidden algorithm result hash: `e2416b6cd3d867df2706257b095eb3a0e3be02adb3d9f59a009a688da01809b9`
- Hidden empirical result hash: `5230cbe44c3885092372b18174e6ef64510f07dac8fcbfa6912f0f0c42ec72f5`

# Aitken GLS BLUE L0 v1 operator audit

Date: 2026-08-25

## Frozen identity

- Task: `aitken_gls_blue_known_result`
- Family: `generalized_least_squares_efficiency`
- Visible question SHA-256: `95946f5c5588f3bfef10038a363467b327680e72bc395abcf711eaa2926f4fe5`
- Visible question hash: `9cc72caef038a2ee127bad74dcebba91c9df6e397ea1249860fcde1c07c6dc5f`
- Gold bundle: `research-l0-aitken-gls-blue-20260825-v1`
- Gold manifest SHA-256: `cb98d48380c2abec6e966f4392d0665c7c4d6778ee11082702ec5c5da1dd86e7`
- Activation commits: `a25ec10ebcbf6830ffa4385ae37a10463bada434`, then binding commit `ccb34f7c280585c19396f43ea400a7ecccd0cacb`
- Runtime head: `ccb34f7c280585c19396f43ea400a7ecccd0cacb`
- Runtime model: `claude-haiku-4-5-20251001`
- Run: `runs/main_worker_research_l0_aitken_gls_blue_20260825_v1_codex_harness_exact_haiku`

Evaluator authority was frozen, calibrated, and pushed before the first product
model call. The task received exactly one canonical product draw and exactly one
hidden evaluation. It must not be rerun, resumed, repaired, rescored, or
resampled.

## Immutable result

The canonical runtime returned `ACCEPTED`. Visible research evaluation and the
pre-frozen hidden theory authority each returned `1/1`; hidden mechanics passed
`7/7`, and the calibrated semantic judge marked `8/8` claims satisfied.
Formalization, generated code, and simulation were not applicable by frozen task
intent and did not execute.

The source-owning TheoryDeveloper used seven model/tool turns to produce a
352-line, 13,772-byte Markdown/LaTeX derivation. The isolated referee used
thirteen turns, wrote a 266-line report, returned `ACCEPT`, and emitted no
blocking finding. The terminal Critic also returned `ACCEPTED`. The run used 22
product model calls: one Architect plan, seven Theory turns, thirteen referee
turns, and one Critic call.

Authoritative artifact hashes:

- Runtime manifest: `9f693352731ba91992ef537816f990402770901387cb403199e3a25ff4e56348`
- Runtime result: `f04e917e8341d6354798188935a117ac400dc8ddcb39f0c0a14cc23fb22f0c9d`
- Gold report: `2f516f696602f8299f89eec9acfb6487d1c8aadf3bc5b1da52f4db014560c1ae`
- Theory document: `61d6d49743d17d57e11ff054aaf8d13ef6b1a26890cdcd07280e6e94c16e7f39`
- Referee report: `0e5a3cbb6100096ead47fc0aea02420ec89858d4f2df97b18dabadf79c3a2f57`
- Evidence ledger: `ae1ce579be9f7aee5c0901b5a7e2b984835cf4d28b0d7b56a782235b58ff0de5`

## What is correct

The active derivation correctly establishes the core Aitken argument under the
stated full-rank and positive-definite assumptions. It derives GLS unbiasedness
and covariance, writes any competing linear unbiased estimator as `A_GLS + D`,
uses `D X = 0` to cancel the covariance cross terms, obtains the positive
semidefinite remainder `D Sigma D^T`, and gives the corresponding contrast and
uniqueness conclusions.

## Operator caveats

The frozen automated pass is not a clean mathematical-quality pass.

1. Candidate Claim 5.3 says that `D != 0` makes `D Sigma D^T` positive definite.
   That is false without full row rank of `D`; the remainder is nonzero positive
   semidefinite. The equality implication needed for uniqueness is still valid.
2. The self-critique repeats the same false strict-Loewner statement.
3. The whitening example takes `W = L^{-T}` after `Sigma = L L^T` while requiring
   `W^T W = Sigma^{-1}`. In general the compatible choice is `W = L^{-1}`.
4. The rank-deficient boundary says the coefficient-estimator constraint becomes
   `A X = X`, which is dimensionally incoherent. For a mean estimator `H Y` the
   condition is `H X = X`; for a contrast estimator it is `a^T X = c^T`.
5. The nonlinear boundary says covariance matrices are not comparable in Loewner
   order. They can be compared; the BLUE theorem simply supplies no universal
   ordering outside the linear-unbiased class. Its Gaussian MLE example is also
   misleading because with known covariance the beta MLE is GLS and is linear.
6. The referee's scratch evidence contained one `REJECTED_CONTRACT` execution and
   one failed Python execution with a broadcasting error, and no successful
   scratch execution. Nevertheless, the final report said all symbolic and
   numerical verification passed without error. The terminal Critic did not
   receive enough raw scratch status to challenge that statement.

These local overstatements do not invalidate the central GLS covariance
decomposition, but they show that the automated referee and hidden semantic
judge were insufficiently grounded. The immutable protocol score remains `1/1`;
the capability record is therefore **pass with operator semantic and referee-
evidence caveats**, not an unqualified theory-validation success.

## Shared future-task correction

Commit `4ebef6c57ea2a279faf59bca2bd29e219be120ba` makes referee scratch status part
of the compact canonical evidence view shown to the terminal Critic. Failed or
rejected scratch remains nonblocking when the mathematics is independently
supported, but the model may not describe it as successful. The change adds no
mathematical parser, GLS rule, extra model call, retry, repair agent, scheduler,
or output patch. Focused regressions passed `71/71`, the broader panel passed
`194/194`, and the complete repository passed `899/899`.

This correction is future-task mechanism evidence only. It cannot alter the
candidate, referee report, hidden judgment, or score of this consumed draw.

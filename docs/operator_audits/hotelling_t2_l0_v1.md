# Hotelling T-squared L0 v1 operator audit

Date: 2026-08-25

## Frozen identity

- Task: `hotelling_one_sample_t2_known_result`
- Family: `multivariate_normal_mean_inference`
- Gold bundle: `research-l0-hotelling-t2-20260825-v1`
- Gold descriptor hash: `1fc935f30b38d24ae9dab5a73f7c7aa4dfc668f6f6d283b9ae6685f67a80379a`
- Estimator contract: `frozen_estimator_execution_contract:5f86c5314b67b91765c5`
- Freeze commit: `dc0d323eca5fe8eecb0f7a28476950e02a8275da`
- Activation binding commit: `4a25311b1ed168f99a41bf9f38dd97975b801aeb`
- Runtime head: `570d78a58bfdb3d22f092ddf02a1808c001c2c25`
- Runtime model: `claude-haiku-4-5-20251001`
- Run: `runs/main_worker_research_l0_hotelling_t2_20260825_v1_codex_harness_exact_haiku`

The visible contract, external evaluator identity, semantic calibration, negative
controls, and activation identity were frozen and pushed before the first
product model call. The task received one product draw and one post-runtime
hidden evaluation. It must not be rerun, resumed, repaired, hidden-evaluated
again, rescored, or resampled.

## Immutable result

The canonical runtime returned `BLOCKED` after 16 outer traces. Visible research
completion and the full-task hidden protocol both returned `0/1`. Formalization
was not applicable and correctly did not execute.

Component evidence is stronger than the full-task score but cannot override it:

- Theory mechanics passed `7/7`; calibrated hidden theory semantics passed
  `9/9` after calibration passed `14/14`.
- The accepted generated estimator passed `8/9` hidden contract checks over 13
  invocations. It failed the visible invalid-request requirement because NumPy
  coercion admitted boolean values that the public contract explicitly rejects.
- Hidden empirical authority passed `9/9` over 12,000 estimator invocations, but
  runtime had not accepted the final simulation evidence.
- The terminal subsystem was `GeneratedCodeSemanticReviewer`, classified as
  `generated_code_semantic_review_packet_invalid`.

Authoritative artifact hashes:

- Runtime manifest: `d53e4a5158a9eca7c99f601fc70616d6dc94ce703c36d05eb31344bf2baba54f`
- Runtime result: `7100837bf25b8a680149e401425da482db24e6a4657fddbd7cf0cc42ea71b477`
- Gold report: `0d2eca983fa15cb2f4edca1d67d91dbbabb251ee8db0ed025aed84d0dbfef520`
- Evidence ledger: `1878cddda2b02edd5fece8bdab26c9201a2d95d2ed70416fa66673d6e3841053`
- Theory document: `ba16f5111368478e6234d298e2870b150a09e213b560cc9b89c021cf56106f71`
- Theory referee report: `c25384ea3a09f1bf21f074d84415075d4750bebaebf9c729bb4a942142e928f8`

## Scientific diagnosis

The model-owned Markdown derives the standard statistic, unbiased covariance,
exact F transform, univariate reduction, affine invariance, and upper-tail
p-value. The independent theory referee reconstructed the result and accepted
the execution handoff.

The theory document nevertheless reports an empirical F mean of `1.408` against
the theoretical `1.044`, then calls the relative error `2.81%`. The referee's
own scratch result was `1.0199`; it identified the candidate discrepancy but
treated it as nonblocking because the analytic result was sound. This is useful
evidence that review is substantive, and also that an accepted theory checkpoint
does not certify every numerical sentence.

The last simulation source used `p * (n-p)/(n-p-2)` as the mean of an
`F_{p,n-p}` variable, introducing an extra factor of `p`. Its confirmatory metric
failed. The isolated reviewer authored substantive revision findings about the
executed source. Those findings never reached the source owner because its two
compact verdict submissions cited deep RFC 6901 paths that were absent from the
review JSON. Runtime failed closed on transport shape rather than promoting the
candidate.

## Harness conclusion

The consumed trace supports two general Codex-shaped corrections for future
tasks, committed in `ea0118067a2f9f2558db300c76c3fd74675725b9`:

1. Scientific analysis stays in model-authored Markdown. Runtime binds the full
   review input, exact source, identities, hashes, lineage, hidden-outcome
   boundary, and verdict consistency; it no longer asks the model to navigate a
   deep JSON-pointer mini-language.
2. When a simulation reviewer returns `REVISE` and says the current source is
   sufficient, the exact source plus the finding returns to the same
   Simulation source-owner session. No Architect route or fresh planning model
   call is inserted.

These are future-task mechanism changes. They do not alter the estimator, the
simulation, the hidden report, or the immutable `0/1` score of this draw.

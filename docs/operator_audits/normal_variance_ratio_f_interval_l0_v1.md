# Normal variance-ratio F interval L0 v1 operator audit

Date: 2026-08-26

## Immutable identity

- Task: `two_sample_normal_variance_ratio_f_interval_known_result`
- Family: `two_sample_normal_variance_inference`
- Frozen task commit: `ef93a91da4f90422790a41f886ad3f5b207c6191`
- Activation identity and runtime head:
  `749bfbaa90c3ad9c219a11981ce11470802499e1`
- Run:
  `runs/main_worker_research_l0_normal_variance_ratio_20260826_v1_codex_review_harness_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  LLM roles; no Sonnet or Opus call
- Runtime result: `BLOCKED` after 12 outer traces
- Automated hidden report: `0/1`; algorithm and empirical harnesses did not run
- Operator disposition: `OPERATOR_INVALID_BENCHMARK`

The task received exactly one product draw and one post-runtime evaluator pass.
Both are immutable. It must never be resumed, rerun, repaired,
hidden-evaluated again, rescored, or resampled.

## Runtime result

TheoryDeveloper authored three persistent Markdown/LaTeX documents totaling 558
lines and 23,173 bytes. An independent referee accepted the theory preflight.
AlgorithmEngineer then produced executable Python three times, but each of three
generated-code reviews requested revision. The final review lineage budget was
exhausted and Architect returned `architect_feedback_route_blocked`. Simulation
never executed. Formalization was correctly not applicable.

The hidden report observed no accepted algorithm handoff, so it did not execute
the candidate algorithm or empirical harness. It did execute theory authority:
mechanical checks passed `7/7`, semantic calibration passed `13/13`, and all ten
semantic candidate claims were marked `SATISFIED`. Those automated results are
preserved but do not repair the benchmark defects below.

## Invalid public contract

The visible ABI requires both interval endpoints to straddle the observed ratio
for every `0 < alpha < 1`. That is not a property of an unequal-degree equal-tail
F interval. For observed ratio one:

| df1 | df2 | alpha | interval (approximately) | straddles one |
| ---: | ---: | ---: | --- | --- |
| 2 | 9 | 0.99 | `[1.313857, 1.355406]` | no |
| 9 | 2 | 0.99 | `[0.737786, 0.761118]` | no |
| 2 | 30 | 0.90 | `[1.2193, 1.6396]` | no |

The interval remains the correct confidence set for the population variance
ratio. It simply need not contain the observed sample variance ratio. A correct
implementation can therefore violate the frozen response shape.

The visible common-scale invariant is also contradictory. Multiplying both
samples by a nonzero constant leaves the ratio and interval endpoints unchanged,
but the two required raw sample-variance response fields scale by the constant
squared. The contract says every response field is unchanged.

Finally, the public text says invalid requests are rejected but does not require
an exception. The generated source returned a typed error object. The hidden
helper counted rejection only when the source raised. This is an evaluator
choice absent from the public ABI.

The hidden reference calibration does not cure these contradictions. Its
candidate validator applies the same straddling condition, while the calibration
cases use only low alpha values where the reference happens to satisfy it. The
reference would contradict that validator on the declared high-alpha domain.

## Theory findings

The main derivation correctly obtains the independent chi-square pivots, their F
ratio, and the confidence-set inversion

`[R / Q_(1-alpha/2), R / Q_(alpha/2)]`.

That is trustworthy component work. Required active documents nevertheless make
three false or contradictory claims:

- As `alpha` tends to one, both endpoints tend to `R / Q_0.5`, not generally
  `R`. The F median is not generally one for unequal finite degrees of freedom.
- The equal-tail F interval is not generally symmetric around `log(R)` when the
  numerator and denominator degrees of freedom differ.
- The implementation document says every response field is common-scale
  invariant immediately after correctly stating that sample variances scale by
  the scale factor squared.

The independent referee explicitly noticed that generic straddling can fail, but
still accepted the task-derived contract. This explains why a calibrated
semantic rubric can pass while missing a false active requirement.

## Harness defects exposed

The run also exposed two cross-task product defects independent of the invalid
statistics contract.

First, a generated-code reviewer probe receives each estimator as the direct
callable `estimators[artifact_id](request)`. Reviewers repeatedly treated the
value as an object with a `.run_estimator` attribute. Those failures occurred in
reviewer-authored probe source before the exact target was invoked, but the old
observation did not identify that origin clearly.

Second, the two AlgorithmEngineer revision visits began without the exact parent
source or raw reviewer findings. They were fresh regenerations, not same-owner
source iteration.

Commit `f6eb861a2484393f550cc29aaa3823f346f17eef` fixes only these shared
mechanisms for future tasks:

1. Probe observations carry the originating tool-call ID, callable contract,
   exact-target invocation status, and failure owner. A reviewer probe defect is
   not target-source evidence.
2. An Algorithm semantic revision restores the exact hash-bound source and raw
   review observation into the existing source workspace, bypasses another
   planning call, and requires changed source before execution.

This follows the useful harness boundary from OpenAI Codex: one model-owned
session, exact tool observations, least-authority review, and explicit origin
lineage. It does not embed Codex runtime, add a second scheduler, create a Repair
Agent, parse statistical formulas, or patch generated code.

## Capability accounting

The automated `0/1` report remains immutable, but this benchmark gives neither
capability credit nor capability blame because the operator contract is invalid.
After consumption, four of 48 draws have trustworthy full-task credit and one
draw is separately marked operator-invalid.

Future-task mechanism evidence is `108/108` across the two affected files and
`917/917` across the complete repository in 70.91 seconds. Compile-all, JSON,
architecture-budget, and diff checks pass. `research_agent_runtime.py` is 24,962
lines and top-level production Python is 149,982 lines. None of that changes the
consumed task.

# Neyman stratified allocation L0 v1 operator audit

Date: 2026-08-26

## Frozen identity

- Task: `neyman_stratified_allocation_known_result`
- Family: `stratified_sampling_allocation`
- Public source: Jerzy Neyman, *On the Two Different Aspects of the
  Representative Method*, JRSS 97(4), 1934
- Gold bundle: `research-l0-neyman-allocation-20260826-v1`
- Gold descriptor hash:
  `8734135bdebe64342d9a20a24dcfb3f9d9db45f2f7f9dee4ecc138cd0bfae162`
- Freeze commit: `08666146d91fc7a91443ed4b7c86028ac86f9b3a`
- Activation binding commit and runtime head:
  `e7bd1646c17bca803a1f3852a295b1e60f801a25`
- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Run:
  `runs/main_worker_research_l0_neyman_allocation_20260826_v1_codex_harness_exact_haiku`

The visible task and external evaluator were frozen, calibrated, committed, and
pushed before the first product-model call. The task received one product draw
and one post-runtime hidden evaluation. It must not be rerun, resumed, repaired,
hidden-evaluated again, rescored, or resampled.

## Automated result

AgentRuntime returned `ACCEPTED`; visible research evaluation and the frozen
hidden authority both returned `1/1`. Hidden mechanics reported `7/7`, and the
calibrated exact-Haiku semantic judge marked all seven claims satisfied.
Formalization, generated code, and simulation were not applicable and did not
execute.

The run used four outer traces and 22 product-model calls: one Architect plan,
ten Theory workspace turns, ten isolated-referee turns, and one terminal Critic.
TheoryDeveloper used ten workspace tools, including three successful scratch
executions. The referee used thirteen tools, including exact document search and
reads, a persistent Markdown report, two successful scratch executions, and an
explicit `ACCEPT`. The terminal Critic repeated that acceptance.

Authoritative artifact hashes:

- Runtime manifest:
  `3721453a2b8793868409f20932d2ce94aacaf3394f04441d3c41f20880637424`
- Runtime result:
  `dacc2bf15cd9722029cff2e78ef2778793563d57d79fad6680bb7f1970f94f1a`
- Hidden-gold report:
  `df41c0922d31ee90d4537281cba8bf2cd27cf18511e1ef6e659a71e13b17652a`
- Theory document:
  `0c6155b35aeb99d667b840e875ed5212e06ec72d655c90482a80e858e524fcb7`
- Referee report:
  `d9d3437b63fef9c9bcb4ba1ffd7adbf63345d6670f03e07792ce9a4ecc37ce0b`
- Evidence ledger:
  `d0f627208cad9a74b64393c2bb8db51cc3cc1daa27ded1eeda9ca4edbfda94ca`

## What is correct

For strictly positive within-stratum standard deviations, the candidate
correctly derives

`Var(mu_hat_st) = sum_h W_h^2 S_h^2 / n_h`,

the continuous allocation

`n_h = n W_h S_h / sum_j W_j S_j`,

and minimum variance

`(sum_h W_h S_h)^2 / n`.

Its Lagrange calculation and its later Cauchy-Schwarz argument use the right
constraint and equality condition. The central all-positive result is therefore
sound.

## Required boundary failure

The visible problem explicitly fixes `n_h > 0` and requires zero-variance strata
to be handled as a limiting or constrained-design case. The candidate instead
calls `n_h = 0` optimal, says zero and one sampled unit are equivalent, and then
allocates the full total `n` over positive-variance strata while assigning zero
to the others (`neyman_stratified_allocation.md:161-191`). That point is outside
the stated feasible set.

Under strict positivity with no positive lower bound, the displayed value is an
infimum approached as zero-variance allocations tend to zero; it is not attained.
If each zero-variance stratum must receive one unit, the positive-variance strata
receive `n - H_0`, so their minimum contribution has denominator `n - H_0`, not
`n`. Sampling zero units also cannot be called equivalent to sampling one unless
the corresponding stratum mean is already known by some separate mechanism.

This is a required-task error, not a peripheral caveat.

## Active variant errors

The unequal-cost section imposes `sum_h c_h n_h = C` but normalizes its formula
with an undefined `n` and `sum_j W_j S_j / sqrt(c_j)`
(`neyman_stratified_allocation.md:216-224`). Lagrange multipliers instead give

`n_h = C (W_h S_h / sqrt(c_h)) / (sum_j W_j S_j sqrt(c_j))`.

Only the proportionality to `W_h S_h / sqrt(c_h)` was correct; the candidate's
display generally violates its own budget constraint.

For sampling without replacement, the candidate writes

`sum_h W_h^2 S_h^2 (1 / n_h - 1 / N_h)`

and then claims the optimum is inherently more complex and lacks a simple closed
form (`neyman_stratified_allocation.md:226-236`). With only a fixed total-sample
constraint and no binding capacity bound, the second term is constant in the
allocation, so the same interior Neyman rule applies. Capacity, lower-bound, or
other binding constraints can make the solution piecewise or more complex; the
unqualified statement is false.

## Reviewer and evaluator failure

The isolated referee explicitly endorsed all three defects. It called the
zero-allocation treatment feasible, called the unequal-cost display correct, and
said finite-population correction has no simple optimum. Its initial purported
Cauchy proof also set `a_h = W_h` and `b_h = S_h`, which contains no allocation
variable and cannot prove allocation optimality. The later candidate comparison
did inspect the correct Cauchy argument, but the referee still returned no
blocking finding.

The terminal Critic inherited the exact referee report and successful scratch
status, then repeated the false acceptance. The separately calibrated hidden
Haiku judge also marked all seven claims satisfied. Thus the automatic `1/1`
remains an immutable protocol artifact but is an evaluator false positive and
does not receive trustworthy capability credit. The aggregate remains `4/45`.

## Harness conclusion

The Codex-shaped mechanism worked as intended: persistent Markdown/LaTeX was the
mathematical authority; the same Theory model owned its file and scratch loop;
an isolated reviewer owned a separate persistent report and tools; artifacts
crossed sessions by hash-bound references; task intent skipped irrelevant code,
simulation, and Lean lanes; and Architect used only two of four outer traces.

This run therefore does not justify a Neyman formula rule, arithmetic parser,
repair model, prompt checklist, extra reviewer vote, retry, or scheduler. The
failure is model-authored mathematics plus model-based judgment under the exact
Haiku evaluation policy. Future disjoint evaluator bundles should include
plausible mixed boundary and constraint errors among their pre-frozen negative
controls, but no post-hoc change can alter this candidate or score.

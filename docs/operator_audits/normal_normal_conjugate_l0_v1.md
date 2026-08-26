# Normal-normal conjugate L0 v1 operator audit

Date: 2026-08-26

## Frozen identity

- Task: `normal_normal_conjugate_predictive_known_result`
- Family: `bayesian_normal_conjugacy`
- Public source: Persi Diaconis and Donald Ylvisaker, *Conjugate Priors for
  Exponential Families*, The Annals of Statistics 7(2), 1979
- Gold bundle: `research-l0-normal-normal-conjugate-20260826-v1`
- Gold descriptor hash:
  `96e597b9c538ad8576f0b7ab0616fd3fbad4be8f5a790cd71f0e60f304c313d1`
- Freeze commit: `b4c52e9a886d86032f420a7fbbde75e30de8252a`
- Activation binding commit and runtime head:
  `a792b7d44f53153852996d3e8c3e32ac0d30d212`
- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Run:
  `runs/main_worker_research_l0_normal_normal_conjugate_20260826_v1_codex_session_exact_haiku`

The visible task and external evaluator were frozen, calibrated, committed, and
pushed before the first product-model call. The task received one product draw
and one post-runtime hidden evaluation. It must not be rerun, resumed, repaired,
hidden-evaluated again, rescored, or resampled.

## Automated result

AgentRuntime returned `ACCEPTED`; visible research evaluation returned `1/1`.
The frozen hidden authority returned `0/1`: executable algorithm checks passed
`12/12`, empirical checks passed `8/8` over 64,000 evaluator invocations, and
theory mechanics passed `7/7`, but the calibrated semantic judge returned eight
`SATISFIED` claims and one `INCONCLUSIVE` claim. Formalization was not applicable
and did not execute.

The run used 19 outer traces, 18 handoffs, 53 recorded runtime observations, and
123 product-model calls. Of those calls, 119 were logged client-tool turns: 13
TheoryDeveloper, 17 Architect-owned referee/metric work, two AlgorithmEngineer,
four generated-code reviewers, and 83 SimulationEvaluator turns. Four direct
calls covered the initial Architect plan, metric semantic reviewer, simulation
planning envelope, and terminal Critic. The 83 Simulation turns were spread
across one initial nine-turn segment, eight more nine-turn segments, and one
two-turn segment, exposing poor same-owner context continuity rather than a need
for task-specific repair logic.

Authoritative artifact hashes:

- Runtime manifest:
  `6e4a68442e73d54278d8cd6edabb9c7c60400aad1f39c19e1cc01ff057d91220`
- Runtime result:
  `8536931e6d7e85158bf1d191faf13d01ea1430fedb644241bfe0b2bf1d4c8c3e`
- Hidden-gold report:
  `1d78f6ea68ff2b5d23c4ec48fab130e6bc3463a45efa683cd2cde2c804e2b607`
- Main theory document:
  `71611932195a8107a0e81d17ee9597c001e6939bcd3be3b7799a426b216dd9d1`
- Estimator theory/interface document:
  `016e89d396e1cb6b5cb17125121624158193aa306985ba57c91b53ac9606635f`
- Independent referee report:
  `470811de75a55c8cea776db013b6d5ecfd5362092fd85501026773fb1d805635`
- Evidence ledger:
  `6dad4e049030e6994618993b72ac27c52159981a710a745480454ccbd74fab4e`

## What is correct

The candidate correctly expands the prior and likelihood kernels, combines
precisions, and derives

`v_post = 1 / (1 / v0 + n / sigma2)`

and

`m_post = ((1 / v0) m0 + (n / sigma2) xbar) / (1 / v0 + n / sigma2)`.

It also correctly derives the posterior predictive distribution with mean
`m_post` and variance `sigma2 + v_post`. The generated estimator implements
these precision formulas rather than the later erroneous named weights, which
is why the hidden executable contract passes. The prior-predictive simulation
also produced calibrated aggregate posterior and predictive coverage and passed
the evaluator-owned empirical checks.

## Required normalization error

The authoritative derivation defines `tau0 = 1 / v0` and
`taun = n / sigma2`. It then writes the prior weight as

`w0 = tau0 / (tau0 + taun) = v0 n / (v0 n + sigma2)`

and the data weight as

`wn = taun / (tau0 + taun) = sigma2 / (v0 n + sigma2)`

at `normal_normal_conjugate_derivation.md:126-130`. Those rational forms are
swapped. Direct simplification gives

`w0 = sigma2 / (sigma2 + n v0)`

and

`wn = n v0 / (sigma2 + n v0)`.

The next line uses `m_post = w0 m0 + wn xbar`, so substituting the displayed
rational forms contradicts the correct precision-weighted mean already derived
at line 124. This is exactly the kind of internally inconsistent intermediate
derivation that a correct final formula or executable implementation cannot
cancel.

## Empirical-design coverage

The main theory document says only that simulation can check posterior and
predictive properties and gives nominal coverage as an example. It does not
make all task-requested prior-predictive diagnostics independently auditable in
the authoritative theory workspace. The later generated simulation does execute
the standardized posterior error, posterior MSE, posterior coverage,
standardized predictive error, and predictive coverage design, so the empirical
dimension passes. The hidden theory semantic judge's one `INCONCLUSIVE` result
and the empirical `8/8` must remain separate evidence rather than being collapsed
into one verdict.

## Reviewer and evaluator failure

The isolated referee reconstructed the correct precision formula, then explicitly
endorsed both swapped rational weights at report lines 160-164 and returned
`ACCEPT`. Its scratch work verified the correct estimator formula, not the
equivalence of the two erroneous simplifications. The terminal Critic accepted
the same theory. The hidden semantic judge did not fully accept the theory, but
its opaque one-claim `INCONCLUSIVE` disposition does not identify or correct the
weight swap. Operator review therefore marks the theory invalid independently
of the already-failed hidden full-task score.

The aggregate trustworthy capability score remains `4/46`.

## Shared harness correction

Commit `39d42c18` changes only shared, future-task mechanisms:

1. TheoryDeveloper is told to give every independently falsifiable requested
   conclusion its own stable claim identity in the Markdown-backed claim graph.
2. The independent referee receives an ordered accountability map derived from
   the active question, claim index, estimator handoff, and task-selected
   simulation or formal targets. Its mathematical work remains one persistent
   Markdown report; the compact terminal envelope contains only component IDs,
   model statuses, findings, and the report reference.
3. Theory, scientific Python/R, and Lean checkpoint windows may replay up to
   eight recent exact complete tool-call/result pairs from the same owner after
   validating the sealed parent transcript. The current hash-bound workspace
   remains authoritative, no summary is generated, and old budget counters are
   explicitly non-authoritative.
4. Algorithm and Simulation coding workspaces receive the same ordinary
   24-turn capacity already used by Theory and referee workspaces. This is a
   ceiling, not a quota or automatic continuation.

The change adds no Bayesian formula, mathematical parser, repair agent, retry,
vote, scheduler, model escalation, output patch, hidden feedback, or mandatory
formal lane. Thirteen unreferenced legacy helpers were deleted, production Python
remains below the existing 150,000-line budget, and the complete repository
passed `911/911`. This future-task mechanism evidence cannot change the consumed
Normal-normal candidate or its immutable `0/1` hidden score.

# Operator audit: randomized distributional transform L0 v1

## Immutable draw boundary

Task `randomized_distributional_transform_known_result` consumed exactly one
fresh product draw and exactly one post-runtime hidden evaluation from product
code head `6e9295de6bf84795fa13fe15362a7c4f085d8887`. All seven enabled
roles used exact `claude-haiku-4-5-20251001`; no Sonnet or Opus call occurred.

The immutable run is:

`runs/main_worker_research_l0_randomized_distributional_transform_20260827_v1_codex_single_loop_exact_haiku`

AgentRuntime returned `ACCEPTED`, and its visible research-loop contract passed
`1/1`. The evaluator-only full-task result is nevertheless `0/1`. Formalization
was correctly not applicable and Formalizer did not execute. This task must never
be rerun, resumed, repaired, hidden-evaluated again, rescored, resampled, or fed
hidden/operator findings as source-owner feedback.

## What executed

The one outer graph used eleven iterations, two same-owner workspace
continuations, and seventeen runtime tool calls:

1. TheoryDeveloper authored two persistent Markdown documents, used Python
   scratch, and explicitly committed a theory checkpoint.
2. An isolated theory referee read the documents, used its own scratch tools,
   and accepted the theory.
3. AlgorithmEngineer authored and executed the estimator; its independent source
   review accepted it.
4. SimulationEngineer authored and executed exploratory and confirmatory source.
   Semantic findings returned directly to the same Simulation owner, without an
   Architect round trip or repair agent.
5. An isolated source reviewer accepted the frozen evaluator source, which was
   replayed byte-identically on the hidden confirmatory cohort.
6. Critic accepted the visible evidence vector and disclosed its remaining gaps.
7. Only after AgentRuntime terminated did hidden theory, algorithm, and empirical
   evaluation run. It generated no runtime feedback.

This is positive evidence for the Codex-shaped single-owner tool loop. It is not
evidence that the mathematical reviewers were reliable enough.

## Operator findings

### 1. An arbitrary-CDF claim is supported only by a finite-discrete proof

The authoritative theory title and setup explicitly target an arbitrary CDF, and
Claim 1 states that

`Z = F(X-) + U * (F(X) - F(X-))`

is uniform on `[0,1]`. The proof at lines 27-84 conditions only on finitely many
events `X = x_j`, sums over `j = 1,...,k`, and uses cumulative sums of point
masses. That establishes the finite-discrete case only. It never treats a
continuous component or a mixed distribution.

The continuous specialization at lines 86-99 then invokes Claim 1 to conclude
the ordinary probability integral transform. Because the preceding proof did
not establish Claim 1 for continuous CDFs, this is unsupported and circular as a
completion of the arbitrary-CDF target.

There is also a smaller endpoint defect in the finite-discrete argument. Adjacent
closed jump intervals share a boundary, so the claimed unique `j*` need not be
unique at CDF jump endpoints. A half-open convention or a separate endpoint
argument fixes the finite-discrete proof, but it does not repair the missing
continuous/mixed case.

The compact problem card silently narrows its assumptions, DGP, and desired
theorem to finite discrete laws while the active Markdown retains the broader
arbitrary-CDF conclusion. Structured handoff scope cannot override an active
mathematical claim. The model reported no corresponding unresolved gap.

### 2. The independent theory referee reproduced the restricted proof and missed the scope change

The isolated report explicitly describes the question as an arbitrary-CDF result,
then reconstructs only the finite-support sum and calls it mathematically sound.
It similarly accepts the continuous case merely "by Claim 1." The reviewer read
the full document ranges, used eleven turns, fifteen tool calls, and three scratch
attempts, so this was not missing context or a stopped tool loop. It was a
mathematical judgment failure.

The frozen hidden mechanical theory harness passed `7/7`. The calibrated
protocol-v9 semantic judge also marked seven claims satisfied and one empirical-
design claim inconclusive; it incorrectly marked the arbitrary-CDF jump-interval
proof satisfied. Operator inspection therefore invalidates trusted theory and
full-task credit even though the automated semantic document status was `PASS`.

### 3. Algorithm and hidden empirical behavior pass as components

The hidden algorithm harness passed `8/8` checks over 28 estimator invocations.
The hidden empirical harness passed `7/7` checks over 16,000 estimator
invocations. These are genuine evaluator-only component results for the frozen
finite-discrete ABI and empirical scenarios.

They do not establish the arbitrary-CDF theorem, and they cannot be fed back into
the consumed product run. The final task remains `0/1` because its required theory
dimension is not trustworthy.

### 4. The Simulation reviewer accepted a disconnected acceptance decision

The frozen evaluator source computes means, variances, bin frequencies, confidence
intervals, discreteness summaries, and KS statistics, but returns
`acceptance_passed: True` unconditionally. In the exact confirmation output, two
of four laws have `bins_within_ci=false`; those diagnostics do not affect the
returned decision.

The independent review explicitly quotes the constant return, calls it correctly
typed and semantically aligned, and accepts with no findings after one terminal
submission and no executable probes. Runtime then reports source-authority binding
as nonvacuous metric evidence because the exact source was independently accepted
and replayed unchanged. The identity and blinding mechanism worked; the model
reviewer's source judgment did not.

This must not be replaced by a runtime AST rule that tries to infer scientific
decision semantics. The shared future fix is to require the existing source
reviewer to trace the returned decision through every load-bearing computed check.
Hidden empirical behavior happened to pass, but that later result cannot make the
visible source-review decision retroactively valid.

## Evidence hashes

- Runtime manifest bytes: `91d81998c91fb74b411ab7553c4bb7b1abd06ed6072ee6670287f527d07d55a2`
- Runtime result bytes: `d628ee06ea1ae7fa2ff755b5c43aefc1794984a26e21424acaaf289c59e99c3c`
- Hidden evaluation bytes: `5a78c4dd3dc4be1816fb09f95b1dd71b0ebaa669e63b8b937ca0ddfab25e95e3`
- Runtime topology bytes: `653d3e8fbf2548499f954c585777d41996844a1434bcf40b71853aadb87f8a82`
- Runtime evidence-ledger bytes: `89369c1dc124ebeeb0b05c49c118cb80c7e4860f0f6c1768b6032800d378d5c2`
- Accepted theory packet stable hash: `68b9c71f1232774044488905d07b9cd7631ce201bbcd873da6fbe77d80e6cde1`
- Accepted theory document set: `b9347d6c136e14f2c33db7a4c56f65ed5666e9affef2d635ab063f10031b4ec6`
- Theory document bytes: `e8a011d292ae4740a52d873b6fd174caa508f1f75a9ccb1d755df00ac70ba002`
- Estimator document bytes: `a520072b33adea2b47ae61cff19040ec08e81efec795c552a407b14608b1e40f`
- Theory-referee report bytes: `2af1fb228167579902abf3995b0a6efafe6a3dc412939d911fed219dee77314d`
- Evaluated estimator source identity: `234c4e4e9cfac7d9151ffd59d1977762177bb5524f55775253db222fb95e506e`
- Confirmatory evaluator source identity: `16c44c05642315d4ad6a988a2e7d19bdee5831c5a7fcda2486ab58aa8d18e795`
- Confirmatory evaluator file bytes: `d361e9a29891e725969c8e456a9a414a5f0ff3e037780be1ab25cb08bbb850e1`
- Simulation source-review document bytes: `a57cfdc5817770b094f84a9b778da61cd720fef78f3e4014045c5723bd34ddb9`
- Hidden theory mechanical result: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden theory semantic result: `516fae49fc0ca0beae4338d89fc60673f164feaffe615b39a9c93c7925d6ace6`
- Hidden algorithm result: `2cf2dc1212061a2bf90924654897a51620d4c481b435a50547548c47562332bc`
- Hidden empirical result: `72dc891629557873d0684c03d58539eace97f89c00dd76e9f99641b8cab18e96`

## Disposition and future-only correction boundary

Operator disposition:

`OPERATOR_INVALIDATED_THEORY_SCOPE_CONTRACTION_AND_SIMULATION_REVIEW_FALSE_ACCEPT`

Trusted full-task capability remains `4/71`.

Commit `02ce1ae3` applies only shared future-task protocol corrections. The
document-backed Theory owner must reconcile active quantifiers and proof branches;
the independent referee and protocol-v10 hidden semantic judge must treat a strict-
subdomain derivation supporting a broader active conclusion as invalid; and the
existing Simulation source reviewer must trace the acceptance output through its
computed checks. Theory documents retain theory-level predictions and assumptions,
while the Simulation owner retains the full executable confirmatory protocol.

This follows the useful OpenAI Codex harness principle: one persistent owner reads
raw tool observations and revises its own work, while validators may block but do
not rewrite content. No Codex runtime, second scheduler, repair agent, source parser,
statistical formula, CDF rule, Python patch, retry, extra model call, or model
escalation was added. Focused tests passed `175/175`; the complete repository passed
`988/988` in 84.96 seconds for the mechanism commit, and the ledger-inclusive
repository passed `988/988` in 86.12 seconds.

The future mechanism commit cannot alter Task 71's immutable `0/1` result.

# Pinball-loss quantile L0 v1 operator audit

## Immutable evaluation boundary

- Task: `pinball_loss_quantile_known_result`
- Product draw: exactly one fresh `research_eval` run with
  `claude-haiku-4-5-20251001` for every enabled role.
- Product status: `BLOCKED` after twelve outer-graph iterations with
  `critic_scientific_inconclusive`.
- Hidden evaluation: exactly one evaluator-only pass after AgentRuntime
  termination.
- Full-task result: `0/1` under the pre-frozen protocol.
- Formalization: not applicable.
- The run must never be resumed, rerun, repaired, hidden-evaluated again,
  rescored, or resampled.

The runtime manifest SHA-256 is
`8296fc8375cce751f4e7c3d4f848dbf670ffe330c943b9170717de61bac6b736`.
The hidden-evaluation artifact SHA-256 is
`1bfade2e7b8965eeeec5e7c55fb4038b40da635cc659efc1f71c21e841cd224c`.
The runtime result, tool-call ledger, and model-topology hashes are respectively
`61124164a6573c36af8a73ae1513bc87aeacaf1dea592adaa34ab7d41e948fef`,
`45a17540e47d9ed536390889b1fa64dac44528d5dd8901041c8b041e3033bd5f`,
and `242010aee8233eabd3c90b24e0e3e53fe105377267e65485083ca8c5c94d6eba`.
Hidden authority remained outside runtime and generated no model feedback.

## What worked

TheoryDeveloper used a persistent Markdown/LaTeX workspace, Python scratch,
independent review, and immutable checkpoints. The lower inverse-CDF statement
and final population minimizer characterization were present. The frozen hidden
mechanical authority reported `7/7`, and its calibrated integrated exact-Haiku
semantic judge reported all seven required claims satisfied.

AlgorithmEngineer authored and executed one complete Python implementation. Its
lower empirical quantile, pinball-loss value, counts, permutation behavior, and
positive affine behavior were numerically correct on the accepted domain. The
hidden algorithm harness passed `9/11` checks. The separate hidden empirical
authority passed `10/10` checks over 18,000 estimator calls. Those empirical
checks remain evaluator-only component evidence because runtime accepted no
confirmatory result.

The final Critic did not promote an executed simulation merely because source
ran. It correctly returned `RESEARCH_CANDIDATE_INCONCLUSIVE` when the realized
simulation evidence did not satisfy the frozen protocol.

## Operator mathematical findings

The active theory is not valid despite both automated theory passes.

First, the derivation differentiates `rho_tau(Y - q)` as though it were
`rho_tau(u)` and omits the chain-rule sign. At an atom it then replaces the
weighted interval `m [tau - 1, tau]` by the symmetric interval `[-m, m]`. The
correct subdifferential in `q` is

```text
partial R(q) = [F(q-) - tau, F(q) - tau],
```

which yields the stated final condition, but not by the displayed argument.

Second, the document says that an atom can make every point in a neighborhood
of the atom minimizing and that continuity alone gives uniqueness. An atom with
`tau` strictly inside its CDF jump ordinarily selects that point uniquely.
Nonuniqueness comes from a flat CDF region at level `tau`; continuity without
strict increase does not exclude such a region.

Third, the empirical uniqueness paragraph reverses the integer-`n tau` case.
When `n tau = k` and `X_(k) < X_(k+1)`, every point in
`[X_(k), X_(k+1)]` minimizes empirical pinball loss. Ties spanning the CDF jump
usually select the tied value rather than an interval of distinct values. For
the sample `{1, 1, 2, 3}` at `tau = 1/2`, the minimizer set is `[1, 2]`.

Finally, negative residual loss is positive: calling overprediction a
"reward" is false. These are active mathematical errors, not stylistic defects.
The hidden rubric explicitly asked for derivative signs, atom/flat-region
behavior, uniqueness, and integer-`n tau` handling, so its integrated semantic
PASS is itself a false acceptance under exact Haiku. No candidate document was
edited after evaluation.

## Algorithm and reviewer findings

The frozen closed contract excludes booleans from both numeric values and
`tau`. Python makes `bool` a subclass of `int`, but the source uses
`isinstance(value, (int, float))` without excluding `bool`. The two failed
hidden checks are the aggregate public-contract gate and invalid-request gate.

The independent source reviewer attempted three probes, but every probe failed
in its own binding/import scaffold before invoking the target implementation.
It nevertheless accepted the source by inspection and missed the boolean
contract defect. This remains a model-owned source-review failure. Runtime must
not add a Python-type corner-case patch or repair the consumed candidate.

## Protocol-to-source drift

The frozen `metric_protocol.md` is internally inconsistent. Scenario 2 declares
20 replicates per configuration while its formulas divide by 200; it claims a
very narrow `[0.45, 0.55]` convergence-slope gate from that small design; and its
declared total does not consistently describe the work required by all listed
scenarios.

The Simulation source then silently implemented a materially smaller study: 260
estimator calls, fewer distributions, quantile levels, sample sizes, and
replicates, plus a relaxed `[0.40, 0.60]` slope gate. Runtime metadata retained
the requested `replicates=2690`; that argument is not evidence that the source
performed 2,690 protocol-bound calls. The simulation semantic reviewer accepted
this translation, while Critic correctly treated the released evidence as
inconclusive.

The general correction is not a task-specific count rule. For future fresh
tasks, the model-authored executable evaluator should become the frozen
preregistration authority, accompanied by a concise human-readable protocol and
independent pre-outcome source review. That removes a lossy Markdown-to-source
translation while preserving blinding, hashes, and evaluator ownership.

## Shared Codex-harness correction

The live Simulation session also exposed an inner-loop mismatch: every exact
source edit immediately launched the entire expensive study. A timeout therefore
made each subsequent model-authored edit trigger another timeout before the model
could finish a coherent revision.

Commit `b567aaa68195e85cc6f799f727b415903251af46` separates the shared Python/R
workspace actions for future tasks:

- submit or exact-edit changes only model-owned source bytes;
- `run_current_scientific_source` explicitly executes the current bytes and
  returns raw sandbox output to the same model;
- `commit_scientific_source` remains a later, hash-bound action after an accepted
  execution observation;
- an unexecuted current source survives durable checkpoint and resume.

This follows the Codex edit, run, observe, revise loop without embedding Codex as
a second scheduler. It adds no scientific content rule, repair agent, Architect
route, retry model, provider, or model escalation. Focused tests passed `17/17`;
the complete pre-ledger repository passed `969/969`. Task 63 was not rerun.

## Disposition

`OPERATOR_INVALIDATED_ACTIVE_THEORY_AND_CODE_RUNTIME_EMPIRICAL_INCONCLUSIVE`

The task receives no trusted full-task capability credit. Correct numerical and
hidden empirical behavior remain scoped component evidence only. Trustworthy
aggregate capability remains `4/63`, and exact development theorem closure
remains `0/2`.

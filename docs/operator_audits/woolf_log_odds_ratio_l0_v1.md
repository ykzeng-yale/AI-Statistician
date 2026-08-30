# Task112 Operator Audit: Woolf Log Odds Ratio

Date: 2026-08-30

## Immutable Evaluation Boundary

Task112 is the sole consumed exact-Haiku draw for
`woolf_two_by_two_log_odds_ratio_interval_known_result`. The visible question was
frozen at commit `854a3fd4`; hidden authority was qualified and the public
preactivation ledger was pushed at `04ae6683` before the first product-model call.

The product run, its two committed theory packets, two independent referee reports,
one post-runtime hidden assessment, and every output are immutable. They must never
be rerun, resumed, repaired, reevaluated, rescored, resampled, manually patched,
exposed to a source owner, or model-escalated. This audit did not return any hidden or
operator observation to the consumed runtime.

## Result

- Runtime status: `BLOCKED` after five outer iterations. The terminal subsystem was
  ArchitectCoordinator with classification
  `architect_theory_execution_preflight_stalled`.
- Full hidden task: failed, 0/1. No candidate qualified for hidden execution.
- Trusted capability credit: 0/1; aggregate becomes 7/112.
- Formalization: not applicable; Formalizer correctly did not run.
- Product model: `claude-haiku-4-5-20251001` only. No Sonnet or Opus call ran.
- Product calls: 72 total, comprising one Architect proposal call and 71 retained
  client-tool turns. TheoryDeveloper used 49 turns and the two isolated referee
  workspaces used 22.
- Tools: 71 executions with three raw errors returned to their current owners.
- Hidden assessment: one invocation, zero candidate evaluations, zero model calls,
  no expected-value disclosure, and no runtime feedback.

## What Worked

The canonical harness exercised real persistent mathematical work:

- TheoryDeveloper used one durable Markdown/LaTeX workspace, wrote and edited one
  authoritative derivation, ran model-authored scratch calculations, inspected exact
  ranges, and committed two hash-bound packets.
- The first committed document had 222 lines and 11,016 bytes. The revised committed
  document had 251 lines and 15,780 bytes.
- Two clean referee sessions inspected immutable theory files and wrote independent
  Markdown reports of 258 and 219 lines.
- Runtime preserved every source hash, report, finding, scratch observation, and task
  transition without editing mathematics or generating a replacement proof.
- The second review closed none of the four prior findings and reported no finding
  progress. The generic stall boundary stopped the lineage after five outer steps.
- Research-eval mode remained conformant, formalization remained not applicable, and
  hidden authority correctly declined to run without accepted theory and code.

These are harness observations, not evidence that the mathematical result was
correctly derived.

## Scientific Findings

The first TheoryDeveloper document reached the requested finite Woolf formulas but
gave an incoherent variance derivation. It differentiated with respect to four cells
as though all four counts were independent, omitted the negative within-row
covariances implied by fixed binomial row totals, obtained a different expression,
and then jumped to the reciprocal-cell formula without a valid equality.

The independent referee correctly detected that the written transition was invalid.
It then made a more consequential error in its own scratch model: the code used a
diagonal covariance matrix for all four cell counts. Within each fixed-total row the
success and failure counts are complements, so their covariance is negative rather
than zero. The scratch result therefore described a different stochastic model. The
referee nevertheless promoted it to four high-severity findings and falsely claimed
that the reciprocal-cell variance overestimates the delta-method variance for balanced
tables.

A correct derivation can parameterize the two independent sample proportions directly,
or retain the full covariance matrix for the four dependent cells. Either route gives
the reciprocal-cell plug-in variance. This operator diagnosis is recorded only in the
audit; it is not a product rule, prompt answer, runtime patch, hidden-evaluator input,
or consumed-task revision.

TheoryDeveloper then behaved exactly as a retained source owner should: it read the
review report and revised its own file. Because the external observation was wrong,
it faithfully moved the document further from the truth, calling the requested formula
a heuristic and claiming that convergence to a non-unit constant was sufficient for a
standard-normal Slutsky result. The second referee retained the original false premise,
found the revised document internally contradictory, and kept all four findings active.

The public question file also contained descriptive metadata saying public source
discovery was enabled, while the actual runtime had no configured source snapshot or
public-discovery tool. Source replication was explicitly not applicable and the frozen
objective supplied the complete known-result contract, so the draw remains a valid
capability failure rather than operator-invalid. The mismatch is still a benchmark
contract weakness: future tasks that require source access must express that through a
structured runtime-enforced task intent, not an ignored descriptive field.

## Shared Future-Task Change

Commit `2e895af1f84dfbfc06c0da692bfc275710047b6b` changes only shared future-task
harness behavior:

1. Referee tool results are explicitly untrusted observations. A successful scratch
   run validates execution of the submitted program, not its encoded stochastic model.
2. Before scratch can support a blocker, the referee is instructed to compare its
   random variables, joint dependence, conditioning, parameterization, and asymptotic
   regime with the exact candidate.
3. A blocker that conflicts with the frozen objective or an available exact source
   must be challenged through an independent derivation and source read; unresolved
   conflict is reported as uncertainty.
4. `READY_FOR_EXPLORATORY_EXECUTION` is explicitly limited to whether the exact finite
   map is coherent and implementable. Proof or asymptotic disagreement can retain a
   theory `REVISE` verdict without blocking diagnostic Python/R execution.

This selectively reuses the OpenAI Codex harness principle that a reviewer must
demonstrate an actionable defect and that transcript and tool outputs are untrusted
evidence. No Codex Core, App Server, provider transport, thread store, Guardian
runtime, scheduler, second reviewer, vote, task formula, content parser, repair worker,
retry, fallback, model escalation, or mathematical patch was added.

## Artifact Identity

- Visible question SHA-256:
  `9df454aa83486e2798a758338ba76c59399e8dec2e89d5b3c3b169106259082a`
- Public preactivation ledger SHA-256:
  `3f5af0c9bc538507f74646369e91cb82bcf68f8bd732d92b48ef4cf90ce003b1`
- Hidden gold manifest file SHA-256:
  `a7eb6e24f32909c927ad51cb8a38ac3cd6d48a0b803d19703fb5eeb73e37fa02`
- Hidden gold stable hash:
  `73cc8e97019d3710e95496ff5f5e011369267ed572564342a26c3e9d9867f76e`
- Runtime result SHA-256:
  `982cca115329991b3c283680e2e72eb0b7bc9751e92512ba33b238d2937dce79`
- Runtime manifest SHA-256:
  `39a70adb83939f87c1092b719bbf374b79009d718a065e9a80fa9aa4b50c9f4d`
- Completion summary SHA-256:
  `2843f6f5a22fa69340a3dbbe3a997d8a4500eee7a2a16c0b77b05109d8737f06`
- Failure summary SHA-256:
  `787055f6daf6d790c1ef718aaeb3dedd0d65f72d6d3f8133ec493bf651e5e02e`
- LLM topology SHA-256:
  `17187b0a4e81aa05fa77c1e5834dae61b166167c74c0c26cb1b33ebc92a341fc`
- Runtime progress SHA-256:
  `9c7095fbb19f1961bcf95955eda849b4c132ec8f97e18421b5ece9d6040f5473`
- Gold assessment SHA-256:
  `547415916e407f3adf758d84f134232e4b31085f8914c8e290bb64d2101ecf9a`
- First committed theory document SHA-256:
  `911f30156c000543dfcb955ba2c07ce372d75db0edec59aea0289818d2b57d62`
- Revised committed theory document SHA-256:
  `ea986f8daddf7e4ef39d7795e4275ad8176ac9f11db66706dacda57c867df359`
- First referee report SHA-256:
  `fa0f6fb8a398ca6aec9c18733d56015f605f87e04c11cbf50be330f08e84b6b6`
- Second referee report SHA-256:
  `84824ed58b4be3307b14b13ffd0063fccff34aae61a812315bb4f3505d0d9cd3`

## Final Disposition

Task112 remains permanently consumed at 0/1. Its persistent Markdown/LaTeX work,
independent reports, scratch observations, and failed hidden gate are retained. No
accepted theory packet, generated implementation, simulation evidence, Critic decision,
formal proof, or hidden candidate evaluation exists. The post-run shared commit
improves future reviewer epistemics and progressive execution but cannot repair or
rescore this draw.

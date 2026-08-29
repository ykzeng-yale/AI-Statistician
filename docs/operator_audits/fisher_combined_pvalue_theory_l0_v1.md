# Task 93 Operator Audit: Fisher Combination Theory Workspace

## Immutable disposition

- Task: `fisher_combined_pvalue_exact_null_theory_known_result`
- Public source: R. A. Fisher, [Answer to Question 14 on Combining
  Independent Tests of Significance](https://doi.org/10.2307/2681650), 1948
- Frozen runtime HEAD: `cad888f239b23c023f4c416d0472d95a98d7b55c`
- Run: `runs/main_worker_research_l0_fisher_combined_pvalue_theory_20260829_v1_codex_source_grounded_exact_haiku`
- Product runtime status: `ACCEPTED`
- Frozen automated full-task result: `1/1`
- Operator trustworthy full-task result: `1/1`, with the caveats below
- Trusted aggregate after consumption: `7/93`
- Runtime model for every product-model response: `claude-haiku-4-5-20251001`
- Formalization: not applicable

The sole product invocation and sole post-runtime hidden assessment are consumed
and immutable. They must not be rerun, resumed, repaired, reevaluated, rescored,
resampled, manually patched, model-escalated, or exposed to the Task 93 source
owner as hidden feedback. No Fisher-specific runtime or prompt change follows from
this pass.

## Frozen authority

Before any product call, the visible question fixed the global intersection null,
mutually independent exact Uniform(0,1) component p-values, the `-2 log(P)`
transformation, the chi-square sum law, the finite upper-tail formula, exact
calibration, the level-alpha result, the `k=1` reduction, endpoint behavior, and
scope boundaries. The visible question SHA-256 is
`9a7fc25b1cd8717281ec341d466bece0b468f01e62b91d16f25c7a491c6c70bc`;
the runtime-visible projection hash is
`2aaaaed8f61abca79b35b36ab1f1adb5383413f745f6dc7cf9fbad4f112c3e62`.

The evaluator-only bundle was calibrated before activation with seven mechanical
checks, six semantic calibration cases, one complete long-form candidate-mode
tail off-by-one near miss, and a seven-claim reference. The sole preactivation
qualification used eight exact-Haiku evaluator calls, passed `6/6` calibration
cases, rejected the near miss, and accepted the reference. The manifest stable
hash is `a6e59a8f2003b43df9ce801aff8de673a3f05dd356f4792290c47bb1e4b271e2`.
No product call occurred before the activation ledger was committed and pushed.

## Product execution

The one invocation consumed three outer graph iterations:

1. One retained TheoryDeveloper session used eight model turns and eight tools to
   create a real Markdown/LaTeX workspace, run model-selected Python scratch,
   write one 314-line derivation, and commit its immutable checkpoint.
2. One isolated theory referee used ten model turns and ten tools. It read the
   exact document, ran its own scratch checks, wrote a separate 253-line report,
   and returned `ACCEPT`. The outer runtime compiled the frozen theory-only route
   directly to Critic without another routing-model call.
3. Critic used twenty model turns and twenty tools, then accepted the research
   evidence contract with formalization correctly marked not applicable.

All 38 product-model response events used exact Haiku. Sonnet, Opus,
AlgorithmEngineer, SimulationEngineer, Formalizer, source replication, repair
workers, retries, fallbacks, and model escalation were zero. Theory scratch is an
author-selected diagnostic inside the theory workspace; it is not a generated
Algorithm or confirmatory Simulation lane.

## Mathematical result

The accepted structured handoff is
`theory_derivation:ab70180b9bdce2fb02f98f3d` with content hash
`f75369bc067263599a329f9462d53037336b04d193591d4de7d21746ff82688d`.
Its authority is a 314-line Markdown/LaTeX document with SHA-256
`6903156402f2444728308d7b4971c052fa2e7e71ca1c9430249115a263cc5379`.
This is direct evidence that Theory mathematics lives in a durable source file;
JSON carries only artifact identity, hashes, intent, and checkpoint metadata.

The hidden mechanical authority passed all seven checks. The calibrated semantic
authority marked all seven claims satisfied and returned `PASS`; its result hash is
`9c377889a9c023f82f71acad62e743926947a8b19a2043542b2b8f89c60024a4`.
No hidden finding entered runtime feedback.

Operator inspection agrees on the load-bearing mathematics:

- `-2 log(P_i)` has cdf `1-exp(-y/2)` on `y >= 0`, hence chi-square with
  two degrees of freedom.
- Coordinatewise transformation preserves mutual independence, so the sum is
  chi-square with `2k` degrees of freedom.
- The upper tail is
  `exp(-t/2) sum_{j=0}^{k-1} (t/2)^j / j!`.
- Continuity gives an exact Uniform(0,1) combined p-value and exact rejection
  probability alpha under the stated null.
- The `k=1` reduction, product ordering, endpoint behavior, and global-null scope
  are correct.

Two non-load-bearing caveats remain. First, the statement that discrete,
nonrandomized p-values may yield a liberal Fisher test is broader than needed: for
independent valid super-uniform p-values, conservativeness is the relevant default,
whereas liberal behavior requires losing validity, independence, or another stated
condition. The document does not use this sentence to extend an exact equality, so
it does not invalidate the frozen claims. Second, the referee's quoted source-line
ranges do not match the final file. Its named claims and equations are present and
its successful scratch run supports the reported numerical values, but location
precision is weaker than the protocol intends.

## Hidden boundary

A scan of product artifacts, excluding the post-runtime gold report, found zero
evaluator-only paths, hidden filenames, hidden reference hashes, hidden claim
identities, or near-miss identities. The evaluator records
`runtime_feedback_generated=false`. Hidden semantic evaluation made one model call
only after AgentRuntime terminated.

## Codex harness conclusion

The run validates the important selective reuse from OpenAI Codex:

- one retained source owner works through model-selected tools and raw observations;
- substantive mathematics lives in ordinary files and immutable checkpoints;
- an independent reviewer receives artifact-only context and cannot edit source;
- the outer harness owns task intent, provenance, permissions, and evidence
  authority;
- not-applicable Python/R, Simulation, and Lean lanes do not become completion gates.

It also shows that the review adaptation is incomplete. The outer graph is sparse,
but 38 inner turns are excessive for this elementary known result. Critic reread the
same theory document eleven times and ran eight searches; the referee produced 253
lines instead of a short findings-oriented report and cited inaccurate line ranges.
These are general efficiency and review-localization diagnostics. They should be
addressed with retained read context, focused model instructions, and clean terminal
submission on a future disjoint task, not with a formula parser, forced call count,
extra reviewer, repair controller, retry, fallback, or imported Codex scheduler.

Embedding Codex Core, App Server, Responses transport, Guardian, thread/worktree
control, SDK, or its multi-agent scheduler would add another owner and control plane
without improving statistical reasoning, hidden authority, Simulation ownership, or
Lean kernel authority. The reusable unit remains the provider-neutral retained
model-tool-observation contract, not the entire Codex product runtime.

## Verification

Ladder regressions passed `91/91`; the complete repository passed `1046/1046` in
82.29 seconds. Compileall, JSON parsing, `git diff --check`, changed-diff secret
scanning, exact artifact hashes, exact-Haiku runtime topology, evaluator-leak
scanning, and the unchanged 149,999-line production Python budget passed.
`research_agent_runtime.py` remains 24,984 lines and `AgentRuntime` remains 1,248
lines. No closeout check made a product or evaluator model call or reran the
consumed task.

## Immutable hashes

- Runtime manifest: `dcd86e1212c082d118972a2d56aa72be779764a7976811ea1bcf8ea5069d7311`
- Runtime result: `01957035c87a39820332e2a65c89a6da4f8ff783c82d503a674c1bff55fc767e`
- Gold evaluation: `a72072ab8e4b9428df0038f97f84900e63ad81e3b10e5899fbbcaaf9f9f68759`
- Runtime topology: `907ab441fcda3bc4e0ff12e953c01605d1a181048ee28d068a7d29f522763eca`
- Evidence ledger: `14106fc676a224f1abfb3e24e67eff318761e29fef681cc5b7c91f53defc3b1d`
- Task handoffs: `fa826ec2b4b7f37a6275e688cc571c735104e13652fbd394207bf65ca58004d8`
- Runtime observations: `a77ac8c6e69186f24c97580a0ab2ed25b5850377dee59d90bdc0a4ee65004b7b`
- Runtime traces: `6f205c9c6da15f53cab2f7e1db88650c8e8d0b3d9090a2103e518cc3295339f7`
- Runtime progress: `f650db4c87792bb019fb368b55f74b0d8f6c6f9093c2dfe0f80c9f00b5010bc2`
- Theory document: `6903156402f2444728308d7b4971c052fa2e7e71ca1c9430249115a263cc5379`
- Referee report: `27290010a0e26154b7953dff20889f3903b5186de0a265e00eb6cdf8eda00a2d`

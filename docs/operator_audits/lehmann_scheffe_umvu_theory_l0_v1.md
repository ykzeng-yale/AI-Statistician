# Task 75 Operator Audit: Lehmann-Scheffe UMVU Theory

## Immutable disposition

- Task: `lehmann_scheffe_complete_sufficient_umvu_known_result`
- Frozen product code HEAD: `75620bf8ff5f0007e8287ac4d68f8c841f9f5c8f`
- Run: `runs/main_worker_research_l0_lehmann_scheffe_umvu_20260828_v1a_codex_theory_workspace_exact_haiku`
- Runtime status: `BLOCKED`
- Frozen automated full-task result: `0/1`
- Operator trustworthy full-task result: `0/1`
- Trusted aggregate after consumption: `4/75`
- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Formalization: not applicable and not executed

This draw, its post-runtime gold report, and all source artifacts are consumed and
immutable. They must not be rerun, resumed, repaired, reevaluated, rescored, or
used as hidden feedback for the Task 75 source owners.

## Execution evidence

The canonical AgentRuntime used six outer graph iterations. One initial Architect
generation was followed by 66 client-tool model turns: 32 TheoryDeveloper turns
and 34 independent-referee turns. The persistent workspace produced one 235-line,
17,403-byte Markdown/LaTeX document, four theory scratch runs across authoring and
revision, two independent referee workspaces, and two direct review-to-source
revision cycles.

No source-replication, generated scientific-code, Simulation, Critic, Formalizer,
Lean, or kernel lane ran. This matches the frozen task intent. The gold process
produced its sole post-runtime report but did not execute hidden theory mechanics
or semantics because no independently accepted theory packet existed.

Key immutable hashes:

- Runtime manifest: `43f10ba5ca26ab1440976317ccd951f21877424106964a876b1b9e8ba4f56b2e`
- Runtime result: `11b9c91e60e7a94233a240b2f6bfea6e55f5085e3392f35aabf8a41b7a30ea9d`
- Gold evaluation: `2c9b8b884f60093a537c66e2c746af644af0fa53df9f1f0a8e974c4e1e3a75fa`
- Final theory document: `37566bf84fb47e0cb6ef0c8f163ced76d7ca6a12d78e783eaa5da0c584b9ea4d`
- First referee report: `45ecbe5d5728e2e2feb578f91c6f82be9a2b7f8f0be415a601086836ed151d9d`
- Second referee report: `2e8ab80910e09efc5ccd7d36af33ee5bc349194f923556fdb241e4c2e88ae8db`
- Runtime progress: `71d26a7e7db488f7df076244bf0c15cb94daad08dd35259cc3becee3f26933c9`

## Mathematical audit

The main Rao-Blackwell, completeness, arbitrary-competitor, and variance-equality
proof skeleton is recognizable, but the authoritative document is not reliable.

1. The purported Uniform(0, theta) counterexample is false. The sample maximum is
   complete as well as sufficient. The proposed witness
   `a(T) = ((n+1)/n)T - theta` is not an admissible completeness witness because it
   depends on the unknown parameter. The document nevertheless marks this claim
   and its sanity check as supported.

2. The document overstates the theorem hypotheses as necessary and sufficient for
   the existence of a UMVU estimator. Complete sufficiency is a sufficient route to
   the stated conclusion. Failure of either hypothesis means this argument no
   longer establishes the conclusion; it does not imply that no UMVU estimator can
   exist.

3. The common Rao-Blackwellized statistic is not constructed rigorously. The task
   asks for one parameter-independent version. The document writes `E[U | T]` and
   then argues separately under each `P_theta`; it never defines
   `delta(t) = integral U(x) kappa(t, dx)` from the common conditional kernel or
   handles the parameter-wise null sets and possible nonintegrable kernel values.

4. The early variance-reduction corollary is worded as comparison with any unbiased
   estimator before the arbitrary competitor has been Rao-Blackwellized and linked
   by completeness. The later main proof has the needed structure, but the earlier
   active claim is too broad.

5. The unresolved-gap section incorrectly says the tower property relies on
   dominated convergence or Fubini. Conditional-expectation tower identities need
   integrability, not that stated interchange argument.

## Referee audit

The independent referee did not provide a trustworthy mathematical gate.

- The first referee noticed an algebraic presentation error but endorsed the
  parameter-dependent completeness witness and the false claim that the sample
  maximum is incomplete.
- The second referee double-scaled the variance of the sample maximum and falsely
  claimed the correct inequality
  `Var(U1) / Var(U2) = 3 / (n+2) < 1` fails for `n = 2, 3`.
- Its own scratch outputs reported empirical and correct theoretical variances
  near 0.125 and 1/6 for `n = 2`, contradicting the referee report. The system prompt
  already required reconciliation of raw observations, so this is a model judgment
  failure, not a missing deterministic statistics rule.

No task-specific algebra, completeness detector, or counterexample rule should be
added to runtime. Production Sonnet may reason better, while exact-Haiku evaluation
must continue to expose this limitation honestly.

## Shared harness finding

The terminal failure was `theory_developer_packet_validation_failed` after a valid
local edit and then repeated malformed calls. The model emitted the nested `edits`
array as a JSON string four times; raw `ClientToolInputError` observations returned
to the same session, but the no-progress gate ended the segment before checkpoint.

Commit `af132404` simplifies future Theory, Python/R scientific-source, and metric
protocol editing to the same flat one-exact-edit-per-call contract already used by
the Lean source agent. It removes nested model-facing edit arrays and 29 net lines.
The model still selects every old and replacement byte; runtime only checks exact
matching, source identity, isolation, and provenance. It adds no repair agent,
retry, fallback, scheduler, content parser, mathematical rule, or model escalation.
This future-task mechanism change does not alter Task 75's score or artifacts.

## Verification

The research-ladder regression passed 73/73 and the complete repository passed
998/998 in 81.37 seconds. Python compilation, JSON parsing, diff hygiene,
production line inventory, and changed-diff secret checks passed. No model or
hidden-evaluator call occurred during evidence closeout.

## Design conclusion

The persistent Markdown/LaTeX workspace, raw tool feedback, direct same-owner
revision, independent evidence boundary, task-intent lane selection, and optional
Formalizer all behaved as intended. The remaining theory bottleneck is primarily
model mathematical judgment and referee reliability, not lack of JSON validators,
Lean rules, or another orchestration layer. The next benchmark should remain
disjoint and known-result based, with one focused theorem and calibrated hidden
authority, after this immutable `4/75` outcome is recorded.

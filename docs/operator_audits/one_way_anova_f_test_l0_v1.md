# One-way normal ANOVA F-test L0 v1 operator audit

Date: 2026-08-26

## Immutable identity

- Task: `one_way_normal_anova_f_test_known_result`
- Family: `one_way_normal_anova`
- Frozen task commit: `52f8a3a5`
- Activation binding and runtime head: `9685cce1f187db754f521b677b08b428d1c4f707`
- Run: `runs/main_worker_research_l0_one_way_anova_20260826_v1_codex_external_context_exact_haiku`
- Runtime model: exact `claude-haiku-4-5-20251001` for all seven enabled
  roles; no Sonnet or Opus call
- Runtime result: `ACCEPTED` after ten outer traces
- Automated hidden report: `0/1`
- Operator disposition: `OPERATOR_FAILED_THEORY`
- Future-task mechanism commit: `6658c7626664b0287eaa1afc3d6cb14252225599`

The task received exactly one product draw and one post-runtime hidden evaluation.
Both are closed and immutable. It must not be resumed, rerun, repaired, hidden-
evaluated again, rescored, or resampled.

Immutable SHA-256 values:

- Runtime manifest: `80232a9b214c6fa85e0dd4f0ff74d43005466f8c24d5272f38caf3b5bd735dfe`
- Runtime result: `f0e7aec83f469047e1602c63f14d6c641d1c9416d531ce55322606a393b636d9`
- Hidden report: `22aabd779649a9a78460c2d8e1310ae286c16aea7eabbdb908f2e1945b1d06a9`
- Main theory document: `a18133477134aedc53dd1c3f0490f218363c4ac890be70d547dc7be5a88e9a5a`
- Independent referee report: `434c3378acfae4c0a91a2ad8af1b37b396908603a86c695fa59866916ad10d1f`
- Frozen runtime metric protocol: `8d9d3bad0203863441b04d070817b49309e9713b8b43e44f6f8919ebb3d6a13b`

## Runtime result

TheoryDeveloper used one persistent source-owning session for sixteen model turns.
It wrote two Markdown documents totaling 502 lines, ran three exploratory
scratchpads, and committed one hash-bound checkpoint. The isolated referee read
the complete documents in six ranges, ran two independent scratchpads, and
accepted. AlgorithmEngineer then authored and executed one Python estimator;
independent source review accepted it after three exact-estimator probes.
SimulationEngineer authored and executed one confirmatory program with 50,000
runtime replicates, and its independent source review accepted. Formalization was
correctly not applicable.

Nine ordinary tool-input failures remained inside their owning sessions: three
Theory document writes/edits, three initial referee searches, and three metric
protocol edit/commit attempts. Each raw error returned to the same Haiku session,
which recovered without Architect routing, a repair agent, or content patching.

The hidden algorithm harness passed `8/8` over 17 exact estimator invocations. The
hidden empirical harness passed `8/8` over four independently frozen Gaussian-null
designs and 12,000 estimator invocations. The accepted source therefore gets
trustworthy scientific-code and empirical component credit. Runtime simulation
also passed all eight preregistered metric contracts.

## Blocking theory defect

The authoritative theory document's `NULL_DIST_1` claim is false. Lines 140-155
state

```text
||Y - mu 1||^2 = SS_between + SS_within.
```

The expansion drops the nonzero term

```text
N (Y_bar_all - mu)^2.
```

The correct orthogonal decomposition under the null is

```text
||Y - mu 1||^2
  = SS_within + SS_between + N (Y_bar_all - mu)^2.
```

Equivalently, the two ANOVA quadratic forms occupy an `(N-1)`-dimensional
centered subspace; a rank-one grand-mean component is needed to complete the
full `N`-dimensional Cochran decomposition. The document later records that the
two displayed ANOVA ranks sum to `N-1`, contradicting its earlier two-component
application of the stated rank-sum-`N` theorem.

The final claims `SS_between/sigma^2 ~ chi-square_(k-1)`,
`SS_within/sigma^2 ~ chi-square_(N-k)`, their independence, and the resulting F
law are correct. A correct headline theorem does not make a false active proof
step acceptable, so the required theory dimension fails.

## Reviewer false acceptance

`NULL_DIST_1` was a named active statement in the Markdown but was absent from
the compact claim index. The runtime-bound reviewer component map therefore
covered six indexed claims but not this intermediate claim. The referee read the
relevant lines and still reported no finding. Critic then relied heavily on that
`ACCEPT` and also missed the contradiction.

The calibrated hidden semantic judge marked all nine task-level rubric claims
`SATISFIED`. That is useful target-fidelity evidence, but it is not a line-by-line
proof audit and cannot establish that every active intermediate statement in the
authoritative documents is true.

The metric review showed the same reasoning risk at lower severity. Its minimal-
design KS rationale refers to "finite-sample discreteness" of an F distribution,
although the F law and its probability-integral transform are continuous. Its
alpha `0.05` interval also labels `[0.0395, 0.0605]` as about three Monte Carlo
standard errors around `0.05`; it is much wider. These errors did not make the
independent hidden empirical checks pass, but they show that a valid schema and a
positive execution do not replace arithmetic review.

## Evaluator provenance defect

The automated `0/1` was triggered by a different issue. Six of seven hidden theory
artifact checks passed; only `theory-document-authority` failed. The accepted
packet had valid document hashes plus
`theory_content_authority=model_authored_markdown_latex_documents` and
`structured_handoff_role=structured_cross_agent_index_and_abi`. Downstream
consumers already derive `document_authoritative=true` from those exact facts, but
the evaluator-only hydration copied documents without projecting the same derived
flag.

This is a generic evaluator false negative, not a reason to rescore the task. The
operator-discovered mathematical defect independently keeps the theory dimension
failed.

## Shared mechanism response

Commit `6658c7626664b0287eaa1afc3d6cb14252225599` changes only future tasks:

1. Hidden theory hydration reuses the canonical document-authority helper, so
   evaluator and downstream consumers see the same derived provenance.
2. TheoryDeveloper must index every active named intermediate inference or
   dependency, not only requested headline conclusions.
3. The existing isolated referee treats the claim index as navigation rather than
   complete scope and audits active inference-bearing statements omitted from it.
4. Critic may not use a preflight `ACCEPT` or claim index as correctness evidence;
   it must independently challenge a decisive document transition.

No new agent, scheduler, retry budget, equation parser, ANOVA formula, generated-
source patch, model escalation, or mandatory formal lane was added. This follows
the useful OpenAI Codex harness boundary: external files are authoritative, the
same model receives raw tool observations, and structured envelopes carry identity
rather than scientific content.

## Capability accounting

This is the forty-ninth consumed scored task and remains `0/1`. Four of 49
consumed tasks retain trustworthy full-task capability credit; the separate
variance-ratio task remains operator-invalid and contributes neither credit nor
blame. ANOVA receives component credit for hidden-validated scientific code and
empirical behavior, but no full-task credit because theory is required.

Future-task mechanism evidence is `184/184` for the focused and architecture panel
and `924/924` for the complete repository in 78.70 seconds. Top-level production
Python remains below its unchanged budget at 149,999 lines. These regression facts
do not alter the consumed run.

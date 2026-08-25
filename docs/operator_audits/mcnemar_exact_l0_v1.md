# Exact McNemar L0 v1 Operator Audit

## Frozen identity

- Task: `mcnemar_exact_paired_binary_known_result`
- Family: `paired_binary_exact_inference`
- Runtime head: `a50a5d18c534a5ebd78a08d11066580cd9732cae`
- Model: `claude-haiku-4-5-20251001` for every enabled role
- Activation commit: `9648fa2b059fddcaa8d76cbb155ef036d989d001`
- Visible question SHA-256: `5f06fdb9c34813b4fb33f2754dac35a374e9b60fba9a3e7abf74b11ebd8c8d7e`
- Gold manifest SHA-256: `92a2ab75e36d7bda98429dd0577627eb17121d3c943820979cd7b6b257e6795e`
- Runtime manifest SHA-256: `a3dfb209966c52a11169a3b7438eada58590487d6a91123851ff4b2b2d59ea18`
- Runtime result SHA-256: `c0bcdcfeedc8ab6c1057640f2e152e7b3c3e9a0cd0ce88c005759a88376b41f7`
- Hidden report SHA-256: `84c4e3f5ec7a3d1f3ec6b9c7a5e8a3190ec0d9e7d66d6b78b78caa5f3502946f`

Exactly one fresh product run and one post-termination gold evaluation were
authorized. They are consumed. The task is permanently `0/1` and must not be
rerun, resumed, repaired, hidden-evaluated again, or rescored.

## Observed execution

AgentRuntime ended `BLOCKED` after three outer traces and two handoffs:

1. ArchitectCoordinator made one compact exact-Haiku plan.
2. RetrievalMemory skipped formal-source retrieval because formal evidence was
   `not_applicable` and handed the public problem context to TheoryDeveloper.
3. TheoryDeveloper used thirteen same-session model/tool turns. It wrote one
   210-line, 10,479-byte Markdown/LaTeX derivation, wrote and revised the compact
   handoff, reread and locally edited its document, then attempted an explicit
   theory checkpoint.

The checkpoint failed structural validation because two estimator response rows
referenced `def.observed_data` and `def.discordant_total`, while those IDs were
present only as headings in the authoritative Markdown and absent from the
compact claim index. The rejected candidate and a content-addressed recovery
checkpoint were preserved. Runtime edited no theory content and created no
Architect repair route.

The failure occurred before independent theory review, AlgorithmEngineer,
SimulationEngineer, terminal Critic, or any hidden component evaluator. The
visible research evaluation and hidden full-task evaluation are both `0/1`.
Formalizer and formal-target review were correctly inactive.

## Mathematical diagnosis

The draft is not merely structurally incomplete. It contains substantive active
errors:

- In the conditional-law derivation it retains only the factor
  `p^k p^(m-k)` and drops the multinomial combinatorial coefficient. It then
  falsely concludes that `N_01 | M=m` is uniform on `0,...,m`; the intended law
  is binomial.
- For even `m`, it states that the binomial CDF at `m/2` equals `1/2`. The atom at
  the center makes that CDF strictly larger than `1/2`, although the capped
  doubled-tail p-value is still one.
- Its conditional-size argument analyzes only the lower tail and obtains an
  `alpha/2` bound while claiming the full two-sided rejection event. The upper
  symmetric tail must also be included to establish the `alpha` bound.
- It describes the attainable exact p-values as a simple grid of multiples of
  `2^-m`; binomial cumulative sums involve binomial coefficients and do not have
  that asserted enumeration.

These are operator findings, not model feedback or an automated mathematical
parser. They establish that bypassing the structural gate would not have made
the theory acceptable.

## Shared harness diagnosis

The final `commit_theory_checkpoint` correctly returned a model-actionable tool
error, but it occurred on the sole terminal-disposition turn. TheoryDeveloper had
configured zero rejected-terminal recovery turns, unlike the existing Lean,
metric-authoring, semantic-review, and theory-preflight workspaces. The retained
model therefore could not respond by choosing the already-existing
`checkpoint_theory_progress` disposition for same-owner continuation.

Commit `1a1f11d993654cef8760d1296701155f9b3c68fd` aligns TheoryDeveloper with the
shared client-tool loop by reserving one rejected-terminal-disposition recovery.
It does not increase the ordinary read, edit, scratch, execution, or outer-loop
budget. A failed terminal commit returns its exact validator observation to the
same session; that model may commit a valid disposition, report a real gap, or
checkpoint partial progress. There is no repair model, packet patch, mathematical
rule, scheduler, or task-specific branch.

Focused client-tool and Theory workspace tests passed `47/47`; the full repository
passed `897/897` in 69.68 seconds. Production Python is 149,999 lines. This is
future-task mechanism evidence only and does not alter the McNemar score.

## Boundary

The run demonstrates persistent Markdown authoring, direct generic file edits,
raw same-session validation feedback, exact-Haiku policy enforcement, task-intent
formal-lane suppression, and honest fail-closed evidence accounting. It does not
demonstrate correct McNemar theory, independent review, Python implementation,
simulation calibration, or full research closure.

# Neyman-Pearson/Bernoulli L0 v1 operator audit

## Immutable outcome

The single authorized exact-Haiku product draw is **failed, consumed, and
closed** at `0/1`. It ran from product HEAD
`cbc3d1b3898a2157c12a2edb20e20febf84cd7cb` in:

`runs/main_worker_research_l0_neyman_pearson_bernoulli_20260825_v1_codex_harness_exact_haiku`

The runtime ended `BLOCKED` after four outer traces and three handoffs. The
visible research loop was `0/1` but mode-conformant. Hidden theory evaluation
did not execute because no theory packet received independent runtime
acceptance. Python/R implementation, simulation, Formalizer, Lean, and Critic
did not run and were not applicable before the theory gate.

All enabled model calls used exactly `claude-haiku-4-5-20251001`. The trace
records 35 client-tool model turns: nine initial TheoryDeveloper turns,
thirteen isolated-referee turns, and thirteen TheoryDeveloper revision turns.
One additional Architect plan generation gives 36 recorded product model
calls. No Opus or Sonnet call occurred.

## What worked

The TheoryDeveloper used a persistent file-backed workspace rather than a JSON
derivation. It authored, inspected, scratch-tested, and explicitly checkpointed
Markdown/LaTeX mathematics. Independent review used a separate model session,
wrote a durable report, inspected the exact candidate, and returned findings to
the same source-owning theory workspace without a RepairAgent or another
scheduler.

The final retained theory document is 262 lines and 12,361 bytes with SHA-256
`95b1cc301196976c04666e13699e693c666ad1ba24442c2080ba7b1bbb240a49`.
The 181-line, 10,242-byte referee report has SHA-256
`8fb0c059bfe986f3133a0e43a967122dec61e4d8d6dd45b4510bc0c383585dbe`.
These are diagnostic model artifacts, not accepted theory or proof evidence.

## Harness failure

The accepted parent packet correctly retained frozen task intent: theory and
gap disclosure were required while code, empirical work, formalization, and
novelty were `not_applicable`. The direct preflight-rejection handoff rebuilt
the question from only `id`, `title`, `description`, and `tags`. The revision
therefore saw an empty task intent, entered the legacy full-handoff contract,
and exposed estimator, theorem, proof-plan, simulation, and formalization
artifacts.

After targeted Markdown edits, Haiku spent its remaining source-owner budget
authoring malformed artifacts for those irrelevant lanes. Validation correctly
failed closed with `theory_developer_packet_validation_failed`; runtime did not
patch, sanitize, route, or retry the candidate. The recovery checkpoint records
13 attempts, no truncation, and rejected-candidate fingerprint
`5420a50b53101b5717449392f313115678785423dc75e5262ddc5602d5e3b682`.

Commit `8c736798bbcf39ef3b91be199c5bc9be05be0f6c` is a future-task-only harness
correction. It uses the canonical question serializer on the direct handoff,
makes frozen task intent veto inapplicable formal handoffs, and exposes only
task-scoped writable structured artifacts in the revision prompt and tool
schema. It adds no formula, theorem rule, mathematical parser, repair agent,
scheduler, retry, turn, or model escalation.

## Mathematical diagnostics

These observations are operator analysis only. They were not hidden-evaluator
feedback and cannot be used to repair or rescore this draw.

The retained candidate still contains a wrong sign on its likelihood-ratio
partition. On the lower-ratio set, the difference `phi_star - psi` is
nonpositive, so multiplying `L < k` reverses the inequality. The document states
the opposite inequality and then concludes the desired global lower bound.

It also claims that any boundary randomization probability gives the same power.
Changing a constant boundary probability changes both size and power. The valid
statement concerns redistributions on a likelihood-ratio tie that preserve the
null boundary integral, not arbitrary changes in that integral.

The referee correctly questioned the original threshold-existence argument but
its report is internally inconsistent. It first claims that
`n=10, p0=0.3, alpha=0.05` selects `c=10` and produces gamma near 8467, then
later computes the valid `c=5` and gamma near 0.0258. Positive binomial masses
and adjacent tail probabilities always bracket every alpha in `(0,1)`. The
report also repeats the candidate's lower-ratio sign error while calling that
proof step correct. Independent Haiku review therefore supplied useful
falsification activity, but not reliable mathematical authority.

## Evidence hashes

- Runtime manifest: `f9be3ec1ea118b8986b7af9ce43a100ab89a1e79f573f4ad1c5f2c9c573da43f`
- Hidden-gold report: `f6e853bb4adb080467c42af6a6cc061b8ffd7e7152c8184fe6b25ecc9f6f5587`
- Runtime progress: `031e683160109c10d3b8d5f37ad5f8822077d61c2e12915580a3e47ddac57bf7`
- Failure summary: `bc4df770bc9386b601068ab12287d513c8a65db66cd03ce6b8164a2ea6e38298`
- Completion summary: `14bd3f0c61dc620db479567e3c791d410a0080edc426f24b8dacac031146b817`
- LLM topology: `5b7b42761b3123dccb813ae71a17f0f6dcf167a3e9f05dae5eb50340f66d0b3c`
- Runtime traces: `7df80f8e33e4eecfbfff9a54f4fbcb7c12ac33cbfbe96b4de66778ca0610fbc7`
- Task handoffs: `df1abd2ebbee4b0c220c68e23f9f09e2d80d4aad592e69b024a8402803d33f77`
- Runtime result: `a7b6783ae3ec46b94e89d1630c46045a4960016aba1d8698d0c1ca26296db898`

The draw may never be rerun, resumed, repaired, hidden-evaluated post hoc,
rescored, or resampled. Regression tests for the shared correction are evidence
for future disjoint tasks only.

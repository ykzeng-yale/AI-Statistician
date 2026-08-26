# Gaussian KDE AMISE L0 v1 operator audit

Date: 2026-08-26

## Frozen identity

- Task: `gaussian_kde_amise_known_result`
- Family: `nonparametric_density_estimation`
- Gold bundle: `research-l0-gaussian-kde-amise-20260826-v1`
- Gold descriptor hash: `70e93c13b7b8450ffb8aa0352bca2418b97b877ca3cfeddb712edba72559e220`
- Estimator contract: `frozen_estimator_execution_contract:bffbd9ef5c8744c6555e`
- Freeze commit: `d7d0fdcdcf1b1adbf09be9d84d0fb959ed84486c`
- Activation binding commit and runtime head: `812de9e8d17d7a499171202d756f4ec93c1ea448`
- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Run: `runs/main_worker_research_l0_gaussian_kde_amise_20260826_v1_codex_harness_exact_haiku`

The visible Parzen-grounded task, external evaluator identity, algorithm negative
controls, three-DGP exact-MISE authority, and semantic calibration were frozen
and pushed before the first product-model call. The task received one product
draw and one automatic post-runtime evaluator report. It must not be rerun,
resumed, repaired, hidden-evaluated again, rescored, or resampled.

## Immutable result

The canonical runtime returned `BLOCKED` at `TheoryDeveloper` after eight outer
traces with classification `theory_developer_reported_gap`. Visible research
completion was `0/1` but mode-conformant. No theory packet reached independent
acceptance, so the hidden theory, algorithm, and empirical harnesses correctly
did not execute. Formalization was not applicable and correctly did not run.
The full task and capability ladder are therefore immutable at `0/1` and `4/44`.

Authoritative hashes:

- Runtime manifest: `dac38e5c61216316a6f7f0c9ffb82e0e58cd5f2fffe1dfec38e27f85619919a8`
- Runtime result: `646bbd9ad48ffe71e28b1612f0439bd72ffc5eb37a41a107ea9dbae3cf0314fa`
- Gold report: `d7f506c6f19051bd78418ceeaa41cd8113f1857192500970ed3d62c7417c543e`
- Evidence ledger: `ebd318442a27a056c901daf76dae1a4c80889bae6b9bcce4375b32a2d23debf0`
- Final theory document: `5fb3c68e3a40c980f0ebb8f22667ac4e3767c746f967bc46374260b52aef7f91`
- First referee report: `325716fa9a8b533720878a0b870abdcec7b4884c4a63a454b43e92ad08814c7a`
- Current referee report: `fc0e1da5abc8cf62a1f9030d894c507f8aeb963a6092ff03607d3d37e7d9191e`

## Mathematical diagnosis

The model authored a 329-line Markdown/LaTeX derivation and used Python scratch
execution. Its AMISE expression differentiates to
`h^5 = R(phi)/(n R(f''))`, but Claim 7.1.1 and Claim 8.3.1 also introduce an
extra factor four. The normal specialization consequently derives
`(16/3)^(1/5) sigma n^(-1/5)`, then asserts the requested
`(4/3)^(1/5) sigma n^(-1/5)` and attributes the contradiction to a possible
normalization convention. Those statements cannot all be true.

The second isolated referee used its own scratch execution and correctly
localized the active error to Claim 8.3.1. It retracted the older claim that
`R(f'') = 3/(8 sqrt(pi) sigma^5)` was wrong and explained that the extra factor
four does not survive differentiation of the stated AMISE. The report therefore
contained the useful current mathematical observation.

TheoryDeveloper did not resolve it. Its terminal gap instead claimed that the
correct roughness was `3/(8 pi sigma^5)`, which is itself false, and treated the
correct `sqrt(pi)` expression as the source of the bandwidth discrepancy. This
is honest gap reporting but not successful theory development. It is model
reasoning evidence, not a request for a runtime formula or arithmetic parser.

## Collaboration diagnosis

The current referee report was persisted as exact Markdown, but the handoff to
TheoryDeveloper retained only compact finding rows. Stable ledger identity kept
the prior finding's old wording while the report had retracted and relocalized
it. The runtime did not fabricate a repair, yet it failed to expose the best
model-authored explanation to the source-owning model.

Commit `36f90f4c1f1bb7851dba9fce5bd3a6438683eb52` fixes that shared boundary for
future tasks. A generic hash-bound UTF-8 loader is now reused by terminal Critic
and Theory revision. The reroute carries the existing persisted report by
path, hash, and byte size; immediately before the Theory session the runtime
verifies the exact bytes, removes the absolute path from model-visible state,
and exposes the Markdown through the existing read-only workspace artifact
tool. Compact JSON remains navigation and immutable ledger identity, not the
mathematical authority.

This follows the useful OpenAI Codex harness principle: persistent files hold
substantive work, one model uses general tools and raw observations in the same
session, and cross-session collaboration uses sparse content-addressed refs.
It does not import Codex app-server, Responses transport, provider logic,
thread manager, or scheduler. It adds no KDE formula, source patch, repair
agent, retry, hidden feedback, model escalation, or extra model call.

The focused collaboration panel passed `284/284`; the complete repository
passed `907/907` in 69.85 seconds. `research_agent_runtime.py` remains 24,998
lines and top-level production Python remains 149,992 lines, both below the
unchanged architecture budgets. These are future-task mechanism results only
and cannot alter this consumed KDE artifact or score.

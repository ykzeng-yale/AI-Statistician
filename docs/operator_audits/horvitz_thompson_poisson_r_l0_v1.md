# Horvitz-Thompson Poisson R L0 v1 operator audit

## Immutable disposition

Task `horvitz_thompson_poisson_total_r_known_result` received one fresh
exact-`claude-haiku-4-5-20251001` product draw and one post-runtime hidden
evaluation. Both are consumed and immutable. Product research completion was
`0/1`, hidden full-task evaluation was `0/1`, and trusted full-task capability
remains `0/1`. Formalization was `not_applicable` and did not run.

The runtime ended `BLOCKED` after 26 traces, nine outer graph iterations, and 17
same-owner workspace continuations. It recorded 71 runtime tool calls, 88 raw
observations, and 25 artifact handoffs. All seven enabled roles used exact
Haiku. There were no Sonnet or Opus calls, provider fallback, automatic model
escalation, second scheduler, or post-run feedback to a consumed source owner.

## Mathematical finding

The persistent Markdown/LaTeX document correctly derives the three core
finite-population identities under mutually independent Bernoulli inclusion:

- unbiasedness of the Horvitz-Thompson total estimator;
- its exact design variance; and
- unbiasedness of the observable design-variance estimator.

The finite-population scope, certainty units, empty realized sample, zero-valued
units, and mixed signs are also handled coherently. These are meaningful theory
components, but the document is not fully reliable as an integrated scientific
handoff.

Section 10 reports ratios labeled as `bias / (4 * SE)` while the displayed
numerical values correspond to a different scaling, then calls magnitudes above
one acceptable. The section correctly labels the run exploratory and says that
confirmatory evidence is still required, but the numerical interpretation is
internally inconsistent. The independent referee declares the entire document,
executable ABI, and empirical verification complete and correct without
identifying that inconsistency or establishing the confirmatory protocol.

Frozen hidden theory mechanics passed 7/7. The calibrated integrated semantic
judge returned `INCONCLUSIVE`: five of seven claims were `SATISFIED`, while the
R ABI/invariants and confirmatory-protocol claims were `INCONCLUSIVE`. Combined
hidden theory therefore failed. The automated result remains immutable; the
operator finding narrows component credit without changing the score.

## Scientific-code finding

The exact evaluated estimator source hash is
`f923086c9a006c26d085d975f16a9f8c881a01e9cf7e06c273425dc22ef62ed9`.
Its total and variance calculations are numerically correct, deterministic, and
non-mutating for valid vector requests. The runtime sandbox passed and the
independent generated-code reviewer accepted the exact source.

Hidden algorithm authority passed 10/12 checks over 27 estimator calls. The
source checks that `values` is numeric, non-list, unnamed, and finite, but does
not reject a numeric matrix. In R a matrix can satisfy those checks while still
violating the visible frozen requirement for an unnamed numeric vector. The
corresponding public-contract check and aggregate algorithm result failed.
Scientific-code capability therefore receives no full-dimension credit.

This finding must not become a Horvitz-Thompson rule, an R matrix detector in the
outer runtime, or feedback to the consumed source owner. The visible contract
already supplied the semantic requirement; source generation and independent
review did not implement or falsify it completely.

## Simulation finding

The Simulation source owner received raw execution observations through the
existing persistent client-tool loop. Across 17 same-owner continuations, the
runtime recorded 68 generated-simulation sandbox calls. The model repeatedly
responded to the interface error about `requested_runtime_replicates` by adding
input validation carrying that phrase, rather than returning the required
top-level field from `run_sandbox`.

No executable metric protocol was independently accepted, no generated
simulation was promoted, and no confirmatory outcome was released. The terminal
Critic correctly remained scientifically inconclusive. The evaluator-only
empirical authority later passed 8/8 checks over 12,000 exact estimator calls
across three independently frozen 4,000-replicate designs. That is strong
component evidence for the estimator behavior, not evidence that the product
runtime completed its empirical lane.

## Codex-harness lesson

The run supports selective reuse of OpenAI Codex harness invariants:

1. One persistent source owner chooses edits and tools.
2. Raw environment observations return to that same model session.
3. Substantive state lives in external, hash-bound artifacts.
4. A committed observation has stable identity across continuation.
5. Terminal or checkpoint continuation never silently replays executed work.
6. Independent collaborators exchange artifact references at genuine evidence
   boundaries instead of routing every local failure through Architect.

It does not justify embedding Codex Core, App Server, Responses transport,
thread storage, provider state, Guardian, worktree management, or Codex's
multi-agent scheduler. Those would create a second orchestration plane around
the existing Anthropic-backed scientific workspaces.

Commit `81349094a4d8b67dbc1e744c7b45aba6a7c448b4` applies a future-only generic
correction. Result-boundary diagnostics now name `run_sandbox`, the required
top-level key and type, and the observed result shape. The hash-bound initial or
resumed observation remains visible to the same source owner, while checkpoint
continuation cannot rerun an already executed source merely because the session
resumed.

The change adds no survey-sampling formula, generated-source patch, hidden case,
R grammar rule, RepairAgent, Architect route, retry, fallback, scheduler, or
model escalation. Task 78 will never be rerun, resumed, repaired,
hidden-evaluated again, reevaluated, rescored, resampled, or supplied its
hidden/operator findings as source-owner feedback. Aggregate trusted full-task
capability remains `4/78`.

## Evidence identity

- Product activation commit: `09eb4bf4244f2f548914442cbf6781ef9766f5b8`
- Runtime manifest SHA-256: `bf532c487a37518896ee255be71a18fa3d718afe34d45e2bbbb9587602302be7`
- Runtime result SHA-256: `75147633d5ce37cbafa242856c17050cf76174cde8ab2bed236ce464283caf54`
- Hidden evaluation SHA-256: `21c495275ea40e339ef56a5a2f168515f1c3cb58963bbb9a24e13ef4ba6a3455`
- Completion summary SHA-256: `ad8377916a3c684f95dbf8918c3ed24bcbdf9522e524abe27b4eef31f2c0a534`
- Failure summary SHA-256: `bdb9285d250797d38674e9c8ac105d7a61fc30ff296823b7e914f75029ea7296`
- Runtime topology SHA-256: `4108acf69cd1ffc5bd82ce965c9a376681d7acbab698a00fb7afd0e13bc82f99`
- Evidence ledger SHA-256: `b82e0a687891cf7bbdfc24c65b3ecde490a6a2cf758d6689691ed503418ac6f9`
- Progress log SHA-256: `1e1e86a27cfac57b55437fd0b6d14b75696aebac8a0d3e334f06248047bfd6a6`
- Accepted theory packet hash: `dc53e911ed44fd0f7ede23502d21afa09e4af104a132680c04cca6c318f0c9ff`
- Accepted theory document-set hash: `4cc67dd9c70e585f4d664d2bd63dbe80801381a9aaf7eaf92db8e56999491399`
- Theory document SHA-256: `274bf6c1ac073c0b59d1e2c426a59969529284a2d86844ebe902a4367cfaa39c`
- Referee document SHA-256: `2a6165e6a830e281867cd924d925ed29128b5e1b09d10f35bd5bba6dd5c22db3`
- Accepted algorithm handoff hash: `d64c10e77ebeab073418ea0f305cb6a80646e46b11cd1fb4b5ab7a3cf0623e08`
- Estimator document SHA-256: `baeb53ab8fa4288f08cd50292d32ac5aec3d0e90f4d2ba146dfd3cee3bb33751`
- Hidden theory result hash: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden semantic result hash: `eeba4fc3234bf973c81da08ec5a0ea4d814ffaa4c5c5191cda5dff2c4e4d644b`
- Hidden algorithm result hash: `223a94bb9b66e27197f42615b15616730539e8bb07ef1b2fa7561fb6b6c00edf`
- Hidden empirical result hash: `fe40d323e8b41acbf8076b7f16c4493650a713b36af4fff761dfde0fd521833a`

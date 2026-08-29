# Task 98 Operator Audit: Gaussian-Mixture Exact EM

## Immutable disposition

- Task: `gaussian_mixture_em_monotonicity_known_result`
- Frozen product code HEAD: `d40f1b5c3473e15e883dcb3095c98e41f4f5542a`
- Closeout evidence commit: `pending_closeout_commit`
- Run: `runs/main_worker_research_l0_gaussian_mixture_em_20260829_v1_codex_workspace_exact_haiku`
- Product runtime status: `BLOCKED`
- Frozen automated full-task result: `0/1`
- Operator trustworthy full-task result: `0/1`
- Trusted aggregate after consumption: `7/98`
- Runtime model for every executed model call: `claude-haiku-4-5-20251001`
- Formalization: not applicable and not executed

The sole product invocation and post-runtime evaluator assessment are consumed and
immutable. They must not be rerun, resumed, repaired, reevaluated, rescored,
resampled, manually patched, model-escalated, or exposed as hidden feedback.

## Frozen authority

The visible question, public Dempster-Laird-Rubin and scikit-learn snapshot,
estimator ABI, task intent, executable reference, behavioral negatives, and
semantic authority were frozen before the first product call. The activation
ledger was pushed to both the work branch and `main`. The runtime-visible question
hash is `c993b3a372670452df91901cd97f2575a3ed07200f73a68591fe089a92fbdf54`,
and the public source snapshot hash is
`557498c685b8f69ae0c2fa439d9cc1bb6e8281870064602ff13a91a5f05f9cf0`.

The schema-v4 executable authority passed 7 theory checks, 11 algorithm checks,
and 10 empirical checks on its frozen reference. Three wrong candidates produced
all five required validator rejections. Protocol v11 retained the first failed
qualification attempt, then qualified an integrated-plus-adversarial exact-Haiku
judge on all 6 retained calibration cases, the polished long-form near miss, and
all 8 reference claims. The successful 16-call qualification was reused after the
runtime; none of its judgments entered product prompts, tools, or observations.

## Product execution

The product used one `AgentRuntime` and model-owned source workspaces:

1. Architect routed the frozen task to TheoryDeveloper.
2. TheoryDeveloper searched and read the public snapshot, maintained a real
   Markdown/LaTeX document, ran two Python scratch calculations, revised locally,
   and explicitly committed its checkpoint.
3. An isolated source-grounded referee accepted the exact theory checkpoint.
4. AlgorithmEngineer read the theory and sources, authored Python, received raw
   execution failures, edited the same file, reran it, and explicitly committed.
5. An isolated code reviewer probed and accepted the exact algorithm source.
6. SimulationEngineer authored and executed a separate scientific source, revised
   it from raw observations, and explicitly committed it for isolated review.
7. Critic inspected the resulting evidence vector and correctly blocked because
   the required empirical lane had no promotable confirmatory evidence.

The runtime produced 10 traces: 9 outer graph iterations plus 1 same-owner
AlgorithmEngineer continuation. It exhausted no global budget and left no pending
task. There were 76 product-model turns: 15 TheoryDeveloper, 10 Architect, 15
AlgorithmEngineer, 16 generated-code reviewer, 9 SimulationEvaluator, and 11
Critic calls. The same sessions executed 97 tools and observed 15 typed tool
errors. Every model turn used exact Haiku; Sonnet, Opus, Formalizer, Lean, repair
worker, fallback, hidden-feedback revision, and model escalation were zero.

## Theory result

The authoritative theory document is 267 lines with SHA-256
`4b63342b45c45f4bf3c791350d02ced34bee71eafb5e38a60db90179edfc6020`.
Its 147-line isolated referee report has SHA-256
`f83b8a8e0d8c40f31557139694643db4986ad8feb4b9028226c1bd7073c3cf5e`.
The accepted packet is `theory_derivation:91f5ed4ac40f9e0f4442f9af`, with hash
`cbb2a3514cde73b0d8cb6af3e928eea6d7cb4fa32fc20d9b3e4a49003aaf5405`.

Post-runtime authority passed all 7 mechanical checks and all 8 calibrated
semantic claims. Operator review agrees with that component result: the document
defines the latent model, responsibilities, exact M step, ELBO/KL identity,
three-link monotonicity chain, fixed-sigma upper bound, and likelihood-value
convergence while explicitly rejecting global-optimum, label-uniqueness, and
unconditional parameter-convergence claims. This is meaningful Theory workspace
evidence, not full-task credit or kernel proof.

## Scientific code result

The accepted AlgorithmEngineer source is 406 lines with file SHA-256
`b4f6f50acaa126f07c46228919942290cca9844056855311a51dc368e70b8f26`.
Its stable evaluated-source hash is
`30ffc4923a729d7fbaf129f7736a642d26c57eddb59f456ee7112c9079cff28d`.
The accepted handoff is
`accepted_algorithm_handoff:6eae9d45781d9c8cac55`, with hash
`43aaf64676c46a261f2cc1d0a5c915599543b4843a2adf939035daef9f51b7bd`.

The hidden harness executed the source 14 times. Nine of 11 checks passed: exact
valid-case reference agreement, output schema, likelihood monotonicity, label
swap, sample permutation, location-scale equivariance, determinism/nonmutation,
parameter accuracy, and likelihood accuracy all passed. The aggregate check and
invalid-request rejection failed. The public ABI explicitly required exactly six
request fields and rejection of extra, missing, malformed, coercible, nonfinite,
or out-of-domain values; the source instead immediately coerced several fields
with NumPy, `float`, and `int` and did not enforce the closed object domain.

The isolated reviewer had the exact public contract and even noted input
validation, but incorrectly treated it as a possible runtime responsibility and
accepted the source. This is a model/reviewer contract-reading failure. It does
not justify an EM-specific validator, source patcher, repair agent, second
scheduler, larger model, or retroactive credit.

## Empirical result

The hidden evaluator invoked the accepted algorithm on 600 frozen datasets and
passed all 10 empirical checks: 3 designs, 200 replicates each, valid outputs,
monotone traces, convergence, mean and weight bias/RMSE, and bias-to-MCSE control.
This is strong component evidence that the valid-domain implementation behaves
correctly on separated mixtures.

The product runtime nevertheless had no eligible empirical evidence. Iteration 6
created the accepted algorithm handoff, but the Simulation manifest's
`upstream_algorithm_handoff_receipt` is empty. SimulationEngineer therefore
generated a second `run_estimator` inside its 335-line source instead of evaluating
the accepted 406-line algorithm. That source executed and passed its exploratory
diagnostics, but `generated_simulation_passed=false` and
`confirmatory_empirical_evidence_eligible=false`. Critic identified the missing
handoff as a runtime coordination failure and blocked the required empirical
dimension. That block is correct.

This is the principal shared harness defect exposed by Task 98: a content-addressed
accepted artifact existed, but the cross-workspace handoff did not bind it into
the consumer task. A future-task correction should preserve the same outer graph
and tools while passing the accepted algorithm `ArtifactRef` to Simulation and
letting the simulation model author an evaluator around that exact source. It
must not regenerate the estimator, add a task-specific bridge, or repair Task 98.

## Codex harness judgment

The Codex-style invariants worked well inside each workspace: persistent
model/tool/observation sessions, stable scoped tools, real files, direct raw
feedback, local edits, explicit commit, and isolated review. The failure occurred
at the sparse collaboration boundary, not because the workspaces needed another
agent framework. AI-Statistician still should not embed Codex Core, App Server,
Responses transport, thread/worktree storage, Guardian, hooks, or its scheduler.

The generic future correction is narrow: preserve content-addressed artifact
identity across the existing handoff and make the reviewer treat the frozen public
ABI as authoritative in both valid and invalid directions. No EM formula, mixture
rule, expected answer, hidden threshold, deterministic source rewrite, retry,
fallback, or additional orchestration plane belongs in product code.

## Immutable hashes

- Runtime manifest: `e7cc13a66351212327390fa2d3c3acc773cdc24bc32269a358396a91fa7587ff`
- Runtime result: `0f66845bac2d9d1c0f36ab3569c19def3fb3bca7d88567602b55fadc79544146`
- Gold evaluation: `dac761c00cfa0b62f9d20d5ac1ba1beec6ad6d322bcd9193f10d743b0f84bb41`
- Runtime topology: `e415482dfe5b7447146e1d0f4c055ab1e5ac98f8deb0db5d6824f5553be3f58e`
- Completion summary: `3b13bd3a98bf9afa8926b9f6502babd5e57f67b2ce5f5628c2860d0a73c20ffd`
- Failure summary: `01b15338e3a3c85584e8f71074e6e97201d56bc308b99966e7afcfa14799a238`
- Runtime progress: `a327d9c796a6df6229b070682a630e749f25f36f746b1a8cf472c3fd831d7359`
- Runtime traces: `9854453c920dbd263f229ca960978003497f260fac5bb3385e9d0294fff68995`
- Evidence ledger: `d77ceddf56c999d521cb64efaa0d97d2b0ec004990700480be467365cc11a9f7`
- Task handoffs: `4da19911d395159d591332ceeaba9d4815222ed40892afa26ff256315e13a8ba`
- Runtime observations: `056563e146075e520e075af8e6453f32379d277de29b3034f49474bda71fd028`
- Outer tool calls: `41414825183721eacd9d0586f88de79e5ea1a05911aca6e281edc1f4eaf5db5d`
- Runtime source snapshot: `a2f41da32896a9d3aa1c658b152862b3be83911df73a21032805dc462add4855`

A product-artifact scan excluding the post-runtime gold report found zero known
evaluator-only paths, filenames, reference hashes, cases, or judgments. The
evaluator records `hidden_expected_values_disclosed=false` and
`runtime_feedback_generated=false`.

## Verification

Focused ladder and gold-authority regressions passed `158/158`; the complete
repository passed `1058/1058` in 80.75 seconds. Compileall, JSON parsing, diff
hygiene, credential scanning, product-source-diff scanning, hidden-leak scanning,
and the unchanged 150,000-line production gate passed at 149,922 lines;
`research_agent_runtime.py` remained 24,957 lines. No verification command made
a product or evaluator model call or reran Task 98.

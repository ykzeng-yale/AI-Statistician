# Kendall tau-a L0 v1 operator audit

Date: 2026-08-26

## Frozen identity

- Task: `kendall_tau_a_independence_known_result`
- Family: `rank_correlation_independence`
- Gold bundle: `research-l0-kendall-tau-20260826-v1`
- Gold descriptor hash: `d9d44aa733ef5d07c4206a0b9a054bca153ed32e890c6f131a6a4ddc5420cfad`
- Estimator contract: `frozen_estimator_execution_contract:7e39e23d5b91b09a75cd`
- Freeze commit: `e6ab1afb4d0796544d79278ff3ee652b961766f4`
- Activation binding commit and runtime head: `9d00edec736611b14d8802433fdda8213d4549a3`
- Runtime model for every enabled role: `claude-haiku-4-5-20251001`
- Run: `runs/main_worker_research_l0_kendall_tau_20260826_v1_codex_harness_exact_haiku`

The visible task, external evaluator identity, mechanical references, four
algorithm negative controls, three-DGP empirical authority, and semantic judge
calibration were frozen and pushed before the first product-model call. The task
received one product draw and one automatic post-runtime hidden evaluation. It
must not be rerun, resumed, repaired, hidden-evaluated again, rescored, or
resampled.

## Immutable result

The canonical runtime returned `BLOCKED` at `CriticEvaluator` after 22 outer
traces with classification `critic_scientific_rejected`. Visible research
completion and the full hidden protocol both returned `0/1`. Formalization was
not applicable and correctly did not execute.

The frozen automated component report recorded:

- theory structure `7/7`;
- calibrated hidden theory semantics `9/9` after `14/14` calibration;
- algorithm contract `9/10` over 23 hidden invocations;
- empirical authority `9/9` over 24,000 estimator invocations;
- runtime empirical completion failed, so the empirical component remains
  `hidden_gold_passed_runtime_not_accepted`.

Operator inspection overrides the automated theory capability interpretation,
not the immutable score: the theory semantic PASS is a false positive. The full
task was already `0/1` and remains `0/1`.

Authoritative hashes:

- Runtime manifest: `86e8d830dbeb2fcab952defad516b0225a9c5c98a1230403e6120ae0521cc2b5`
- Runtime result: `412ab04b077178dbc37d239a782d5b5d0895817aa77aa405dd211735d42f04c2`
- Gold report: `14d9aa18ba1a1714bd35f7a04973509f10cbf939dfa38aec21559adc8b91fbf4`
- Evidence ledger: `e10d91be92ac02bb2e7915cb6b2789369b0169937f1a6f586030b956a246bc3d`
- Theory document: `3fd3f60c8a7459e4fbeb74a22cf10abb7e1aa9e7ab16a5d7171ed32554154a49`
- Theory referee report: `f3b7d5b8369c27c8d9f2f4e84f53a4efd5706256535baebef663a4e88c4d3d05`
- Metric protocol: `62edd9b9b0f37ace553ce59b5bd4894cabd2230168ebc9f48a6851d34fcf5540`
- Hidden-evaluated estimator source hash: `72251f96bf4324e5379327d8bdcb1af30b33a3ad36f6edc919e4c39ce612f380`

## Mathematical diagnosis

The Markdown document states the correct shared-index product expectation
`E[h_ij h_ik] = 1/9` at line 125, then replaces it with the false value `1/3`
at lines 289-328. Direct conditioning gives `1/3` for each coordinate's two-sign
product, so independence of the X and Y coordinates gives `1/9` for the kernel
product.

The document also undercounts overlapping unordered pair-pairs. Every triple
contributes three, not one, overlapping pair-pairs before the factor two from
the square expansion. Section 6 combines the false covariance with the missing
overlap multiplicity and reaches the standard final variance only because the
two errors cancel.

Both model-owned scratch sessions exposed the contradiction. TheoryDeveloper's
successful run reported `E_h_ij_h_ik=0.111111...`, expected `0.333333...`, and
`match=false`. The isolated referee's run likewise reported `0.111111...` and a
variance mismatch. Its Markdown report then misread `0.111111...` as `1/3`, and
a later scratch program merely verified an expression that already embedded the
wrong `1/3`. The referee changed `REVISE` to `ACCEPT`, and the calibrated hidden
Haiku judge also accepted all nine claims.

This is not evidence for a missing Kendall formula guard. The authoritative
mathematics already lived in Markdown/LaTeX; both source owner and isolated
reviewer had exact reads, Python/SymPy scratch, raw observations, and explicit
instructions to reconcile contradictions. Exact-Haiku reasoning failed despite
the correct harness surface. Production serious theory and mathematical review
remain Sonnet roles; this evaluation intentionally used Haiku everywhere under
the frozen test policy.

## Code and empirical diagnosis

The estimator executed and was independently reviewed, but its input conversion
applies `float(xi)` to every value. Python booleans and numeric strings therefore
cross the public boundary even though the visible contract explicitly requires
their rejection. The hidden invalid-request check caught this; no post-run source
edit is permitted.

The generated estimator's hidden empirical behavior passed all nine calibrated
checks across three null DGPs. That component evidence does not establish runtime
completion, semantic source acceptance, or correct theory.

The model-authored metric protocol selected 5,000 replicates and eight required
rows. Its null-variance rationales describe half-widths near `0.00027` at n=50
and `0.000130` at n=100, but the stored bounds encode half-widths about ten to
forty times smaller. The independent metric reviewer accepted the inconsistent
arithmetic. The final empirical variances were compatible with the hidden
MCSE-calibrated authority but failed those malformed runtime gates.

The protocol also says each DGP must be reported separately while binding each
metric to one scalar path. Generated simulation sources alternated between
pooling DGPs and trying to satisfy the prose, and the reviewer repeatedly used
the old `PARENT_ARTIFACT_CHANGE_REQUIRED` label even while saying the defect was
local to the current Simulation source.

## Harness conclusion

Commit `a5551714` applies only cross-task Codex-style lifecycle corrections:

1. A non-evidence authoring diagnostic uses at most 128 replicates and returns
   raw execution and metric shape to the same source owner. Frozen acceptance
   outcomes are not a source-commit condition. Exact committed bytes still run
   once at the complete frozen confirmatory count, with outcomes withheld.
2. Any nonempty scientific workspace failure makes the last executed source
   ineligible for promotion. A source that exhausted tools or never explicitly
   committed can no longer reach independent review as if it were accepted.
3. Review disposition names now say exactly
   `CURRENT_SOURCE_REWRITE_SUFFICIENT` or
   `CROSS_ARTIFACT_RESOLUTION_REQUIRED`, so a local Simulation rewrite stays in
   its source-owning session without an Architect routing call.

The change adds no statistic-specific formula, parser, source patch, repair
agent, hidden feedback, retry, scheduler, model escalation, or relaxed evidence
gate. The complete repository passed `905/905`; `research_agent_runtime.py`
remains below its regression budget at 24,998 lines. These are future-task
mechanism results only and cannot alter this consumed Kendall artifact or score.

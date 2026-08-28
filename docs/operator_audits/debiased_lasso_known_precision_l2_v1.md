# De-biased Lasso known-precision L2 v1 operator audit

## Immutable disposition

Task `debiased_lasso_known_precision_paper_to_code` received one fresh
exact-`claude-haiku-4-5-20251001` product draw and one post-runtime hidden
evaluation. Both are consumed and immutable. Product research completion was
`0/1`, hidden full-task evaluation was `0/1`, and trusted full-task capability
remains `0/1`. Formalization was `not_applicable` and did not run.

The runtime ended `BLOCKED` after 16 traces, 11 outer graph iterations, and five
same-owner workspace continuations. It recorded 49 runtime tool calls; the
detailed client-tool log records 183 model turns. All seven enabled roles used
exact Haiku. There were no Sonnet or Opus calls, provider fallback, automatic
model escalation, second scheduler, or post-run source feedback.

## Mathematical finding

The persistent 225-line Markdown/LaTeX theory document is substantive, but it
contains several load-bearing errors and direct contradictions.

The Lasso objective at lines 14-17 implies
`X^T(X beta_hat - Y)/n + lambda v = 0`, or equivalently
`X^T(Y - X beta_hat)/n = lambda v`. Lines 19-27 instead give the opposite sign.
Lines 120-123 later state the correct condition, while lines 192-198 return to
the wrong sign and label it `PASS`. The document therefore contradicts itself
on the KKT identity used by the estimator.

The remainder bound at lines 64-75 uses
`||beta_0-beta_hat||_infinity`; the required Holder bound uses the L1 error.
It then combines an unsupported infinity-norm rate into
`O(s_0 (log p)^(3/2)/sqrt(n))` but still claims that
`s_0=o(sqrt(n)/log p)` makes this expression vanish. That conclusion does not
follow from the document's own rate. Lines 52-58 also call the complete
root-`n` estimator conditionally Gaussian with mean `Delta_j`, even though the
remainder depends on the noise through `beta_hat`. Only the score term has the
stated exact conditional Gaussian law.

The independent referee repeats the wrong KKT sign at lines 79-92 and calls the
document internally consistent. It also treats the finite equality
`s_0=3` as satisfying the asymptotic little-o statement and even evaluates
`3=o(16/log(320))`, where `16/log(320)` is about 2.78. The report is not
trustworthy mathematical evidence.

The frozen hidden theory mechanics passed 7/7. The calibrated hidden semantic
judge returned `INCONCLUSIVE`: seven of eight claims were marked satisfied and
the confirmatory-protocol claim was inconclusive. Operator review additionally
invalidates the positive KKT and remainder assessments. Automated fields remain
immutable, but receive no theory capability credit.

## Scientific-code finding

The exact accepted estimator source hash is
`8680b1cf4015d8d3cc35c98903c07f7c6d878b135604934dc410a7e1099bb971`.
Its numerical de-biasing calculation is strong component evidence: the hidden
numerical recomputation and deterministic/non-mutating checks passed, and all
five hidden empirical checks passed over 3,000 exact estimator invocations.

The source nevertheless violates the visible frozen execution contract. It does
not require the exact request-key set, silently coerces values through NumPy and
Python numeric constructors, accepts values such as booleans or numeric strings
that the contract forbids, and does not enforce the declared design dimensions
and strict JSON types. The hidden aggregate public-contract check correctly
failed. Hidden algorithm authority therefore passed only 2/3 top-level checks
over 22 calls, and scientific-code capability receives no credit.

## Confirmatory-authoring deadlock

The initial confirmatory source ran with the runtime's 128-replicate authoring
diagnostic. Independent review correctly rejected applying the frozen scientific
acceptance gate below the visible minimum of 1,000 replicates. The same
Simulation source owner then revised its code to refuse or withhold acceptance
at 128 replicates.

The harness repeatedly executed the same 128-replicate authoring diagnostic and
treated `metrics.acceptance_passed=false` as a tool failure. The source owner
could not simultaneously honor the frozen minimum and make that diagnostic
scientifically pass. Eight later diagnostic executions therefore produced no
promotable manifest, and the runtime blocked. This is a shared harness defect:
successful execution and valid output shape are tool outcomes; scientific
acceptance is a separate frozen gate.

## Codex-harness lesson

The run supports selective adoption of Codex invariants, not embedding Codex
Core or App Server. One persistent Theory, Python/R, Simulation, or Lean source
owner should choose actions, receive raw tool observations, and revise in the
same session. The harness should centrally preserve exact frozen authority,
content hashes, permissions, tool lifecycle, and clean termination. Independent
review remains an artifact boundary, not another scheduler.

Two future-only shared corrections are justified:

1. A frozen execution contract must cross Theory and Algorithm handoffs by exact
   immutable reference and hash. A model-authored explanatory summary may be
   added, but it cannot replace or weaken the authoritative contract.
2. An authoring tool call succeeds when the source executes and returns a valid
   result envelope. `acceptance_passed=false` is a scientific observation, not
   a transport or execution error. Confirmatory promotion still requires the
   separately frozen scientific gate.

No de-biased-Lasso formula, source patch, hidden case, deterministic math parser,
new agent, retry, fallback, scheduler, or model escalation is justified.

Task 77 will never be rerun, resumed, repaired, hidden-evaluated again, rescored,
resampled, or supplied its hidden/operator findings as source-owner feedback.
Aggregate trusted full-task capability remains `4/77`.

## Evidence identity

- Runtime manifest SHA-256: `23a85c3fab4832dbf6a668b855fc65382554d2681a6428d31d8b39cd224c3cb2`
- Runtime result SHA-256: `1eb834dbb27f3f0dfe4bdc73147fd0e982b46ddcf6b037fa75b857ee6f76cc09`
- Hidden evaluation SHA-256: `bed81b1f7d18b13dde50f7065386c24697693bc9d6c16c494ee0c8fc73b455a7`
- Runtime topology SHA-256: `e2b864489506b19be6b807d4ddaa1232a05d654d8bd358d87f55beb17d068f3e`
- Evidence ledger SHA-256: `b60b2d7f70db8f95855d051e2e306b710027b6be4cbdcaca01e8bb2c76c42698`
- Failure summary SHA-256: `2b8b0c5fc91ec56d30df1bf26d03c0e03f4dec0c421f16565b54cd38afc68752`
- Completion summary SHA-256: `ad76abb0807bdff6f2bf6c7b536cedd7555d84ea6ea4ddcc5333190d2802fc11`
- Progress log SHA-256: `3d51f47e8d61e7c7160ebe1b81f764627f06b5a6f27ac046b34589dfcbe41627`
- Theory document SHA-256: `a04aa1e619529f0253e674d60549a7ae3b3f3e0a445268d8f11d1ca768e5110f`
- Referee document SHA-256: `53020b72ac23f4b8ec2503a5cd96775d72510198effefc0952c4a444c62fd0dd`
- Accepted estimator source hash: `8680b1cf4015d8d3cc35c98903c07f7c6d878b135604934dc410a7e1099bb971`
- Hidden theory result hash: `2448162397b7703a7f48b7085f566f96c6179c7bac3eeaf4f72af86fd45a11b6`
- Hidden theory semantic result hash: `d53c193eb2fb22ccb40950a33c6c7cf908503aa727f09a817b9aac316098a182`
- Hidden algorithm result hash: `f7ca75fce9f877df7f443aab49b73c49651f0adf676e979994ef4aa70a88da97`
- Hidden empirical result hash: `c008a0338d5f948ddd35a35cb76fad5ca13d822b5e0ce0246300e68d6edafbe1`
